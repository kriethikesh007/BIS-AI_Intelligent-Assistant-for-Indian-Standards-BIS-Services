import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
import requests

from config import Config

logger = logging.getLogger("bis_ai.services.grok")


class _ChoiceMessage:
    def __init__(self, content: str, reasoning: Optional[str] = None):
        self.content = content
        self.reasoning = reasoning


class _Choice:
    def __init__(self, message: _ChoiceMessage):
        self.message = message


class _ChatCompletionResponse:
    def __init__(self, choices: List[_Choice]):
        self.choices = choices


class _GrokCompletions:
    def __init__(self, service: "GrokService"):
        self.service = service

    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1000,
        timeout: float = 20.0,
        **kwargs
    ) -> _ChatCompletionResponse:
        content = self.service._call_chat_completions_http(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        if content is None:
            return _ChatCompletionResponse(choices=[])
        return _ChatCompletionResponse(choices=[_Choice(_ChoiceMessage(content))])


class _GrokChat:
    def __init__(self, service: "GrokService"):
        self.completions = _GrokCompletions(service)


class _GrokHttpClient:
    def __init__(self, service: "GrokService"):
        self.chat = _GrokChat(service)


class GrokService:
    """
    Official xAI Grok API Client & Resilient LLM Service for BIS-AI.
    Reference: https://docs.x.ai/

    Key Capabilities:
    1. Direct integration with xAI Grok API (https://api.x.ai/v1/chat/completions)
       with backward compatibility for GroqCloud (api.groq.com/openai/v1).
    2. Intelligent system prompt grounded in Indian Standards (BIS Act 2016).
    3. Context-aware synthesis: combines user query, conversation history,
       predicted intent, and retrieved catalog evidence.
    4. General BIS concept explanation without requiring exact dataset matches.
    5. Zero hallucination of standard numbers, fees, clauses, or mandatory orders.
    6. Sanitized diagnostics and robust HTTP error/timeout handling.
    """

    SYSTEM_PROMPT = """You are BIS-AI, an authoritative, intelligent AI assistant for Indian Standards and Bureau of Indian Standards (BIS) services (under the BIS Act 2016).

CORE RESPONSIBILITIES:
1. ACCURATE BIS EXPERTISE: Provide clear, structured, and helpful explanations of Indian Standards (IS codes), product certification (ISI Mark / Scheme I), Compulsory Registration Scheme (CRS / Scheme II), Foreign Manufacturers Certification (FMCS), Hallmarking (HUID), laboratory testing, and consumer redressal rights.
2. EVIDENCE GROUNDING: When AUTHORITATIVE CATALOG EVIDENCE is provided below, treat it as verified ground truth. Cite standard codes (e.g., IS 4151, IS 10322), titles, scopes, certification schemes, and clauses accurately.
3. GENERAL CONCEPT EXPLANATION: If no specific catalog record is provided, or the question is conceptual (e.g., "What is BIS?", "What is conformity assessment?", "What are the steps to apply for certification?", "Difference between ISI and Hallmarking"), explain the concept authoritatively using your verified knowledge of BIS. Do NOT state "insufficient data" when a standard BIS concept or procedure can be explained clearly.
4. ZERO FABRICATION GUARANTEE: NEVER invent, fabricate, or guess Indian Standard numbers, gazette QCO dates, certification fee amounts, clause citations, laboratory names, or non-existent URLs.
5. HONEST UNCERTAINTY & OFFICIAL DISCLOSURE:
   - If asked whether a specific uncataloged product has a compulsory certification order (QCO), explain how to verify via the official BIS Compulsory List / Gazette rather than guessing.
   - If asked for exact current license fees or laboratory testing tariffs, state that exact fees vary by product scale (with MSME/startup concessions) and direct the user to verify at the official Manakonline portal (https://www.manakonline.in).
   - If a product description is ambiguous (e.g. "electrical products" or "electronic devices"), explain the relevant categories and politely request specific product details.
6. UNCATALOGED OR SPECIFIC PRODUCT INQUIRIES:
   - When the user asks about a specific product (e.g. "wired mouse", peripherals, custom electronics, etc.) and NO matching standard is present in the provided catalog evidence:
   - NEVER fabricate, invent, or guess Indian Standard (IS) numbers (e.g., do NOT invent IS numbers, and do NOT cite unrelated standards like IS 4151).
   - Explain what technical parameters are needed to identify the applicable standard (product interface e.g. USB-A/USB-C, voltage/power, intended use).
   - Explain the certification framework: clarify whether standard input peripherals fall under compulsory CRS (Scheme II) or voluntary ISI mark (Scheme I).
   - Explain that exact standards should be searched and verified on the official Manakonline portal (www.manakonline.in -> 'Know Your Standards').
   - Conclude by asking polite follow-up questions to clarify their product details.
7. CLARITY & STRUCTURE: Use concise, professional bullet points where appropriate.
8. LANGUAGE: Respond strictly in the TARGET LANGUAGE indicated (English, Hindi, or Tamil). Keep technical standard codes (e.g., IS 4151, HUID) intact."""

    def __init__(self):
        self._load_config()
        self.last_status: Optional[int] = None
        self.last_error: Optional[str] = None
        self.last_request_succeeded: Optional[bool] = None
        self._client: Optional[Any] = None

    def _load_config(self):
        """Loads and normalizes API configuration from environment and Config."""
        self.api_key = (
            os.getenv("GROK_API_KEY", "").strip()
            or os.getenv("XAI_API_KEY", "").strip()
            or os.getenv("GROQ_API_KEY", "").strip()
            or Config.GROK_API_KEY
        )

        explicit_base_url = (
            os.getenv("GROK_BASE_URL", "").strip()
            or os.getenv("GROK_API_BASE_URL", "").strip()
            or Config.GROK_BASE_URL
        )

        explicit_model = (
            os.getenv("GROK_MODEL", "").strip()
            or os.getenv("GROQ_MODEL", "").strip()
            or Config.GROK_MODEL
        )

        if explicit_base_url:
            self.base_url = explicit_base_url.rstrip("/")
            self.provider = "custom"
            self.model = explicit_model or "grok-2-latest"
        elif self.api_key.startswith("gsk_"):
            self.base_url = "https://api.groq.com/openai/v1"
            self.provider = "groq"
            self.model = explicit_model if explicit_model and explicit_model != "grok-2-latest" else "openai/gpt-oss-120b"
        else:
            self.base_url = "https://api.x.ai/v1"
            self.provider = "xai"
            self.model = explicit_model or "grok-2-latest"

        self.timeout = float(os.getenv("GROK_TIMEOUT", Config.GROK_TIMEOUT))
        self.max_tokens = int(os.getenv("GROK_MAX_TOKENS", Config.GROK_MAX_TOKENS))
        self.temperature = float(os.getenv("GROK_TEMPERATURE", Config.GROK_TEMPERATURE))

    def is_available(self) -> bool:
        """Checks if API key is configured and not running in automated offline test mode."""
        if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING", "").lower() in ("true", "1"):
            return False
        key = self.api_key or os.getenv("GROK_API_KEY", "").strip() or os.getenv("GROQ_API_KEY", "").strip()
        if not key or len(key) < 8:
            return False
        lower_key = key.lower()
        if lower_key.startswith(("your_", "replace_", "placeholder", "test_", "demo_")):
            return False
        return True

    def _get_client(self) -> Optional[Any]:
        """Initializes and returns the client instance if available."""
        if not self.is_available():
            return None
        if self._client is None:
            self._client = _GrokHttpClient(self)
        return self._client

    def get_diagnostics(self) -> Dict[str, Any]:
        """Provides safe operational status without exposing secrets."""
        masked_key = None
        key = self.api_key or os.getenv("GROK_API_KEY", "").strip() or os.getenv("GROQ_API_KEY", "").strip()
        if key:
            if len(key) > 8:
                masked_key = f"{key[:4]}...{key[-4:]}"
            else:
                masked_key = "****"

        return {
            "api_key_configured": bool(key and not key.startswith("replace_with")),
            "masked_key": masked_key,
            "provider": self.provider,
            "base_url": self.base_url,
            "endpoint": f"{self.base_url}/chat/completions",
            "model": self.model,
            "timeout_seconds": self.timeout,
            "max_tokens": self.max_tokens,
            "last_status_code": self.last_status,
            "last_request_succeeded": self.last_request_succeeded,
            "last_error": self.last_error,
            "is_available": self.is_available()
        }

    def _call_chat_completions_http(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        timeout: float
    ) -> Optional[str]:
        """Direct HTTP client implementation using requests."""
        key = self.api_key or os.getenv("GROK_API_KEY", "").strip() or os.getenv("GROQ_API_KEY", "").strip()
        if not key:
            return None

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        try:
            logger.info(f"Sending Grok API HTTP request to {endpoint} (model: {model})...")
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=(5.0, timeout)
            )
            self.last_status = response.status_code

            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices and len(choices) > 0:
                    msg = choices[0].get("message", {})
                    content = msg.get("content")
                    if (not content or not content.strip()) and msg.get("reasoning"):
                        reasoning = msg.get("reasoning", "").strip()
                        content = reasoning.split("\n\n")[-1] if "\n\n" in reasoning else reasoning

                    if content and content.strip():
                        self.last_request_succeeded = True
                        self.last_error = None
                        return content.strip()
                    logger.warning("Grok API response contained empty message content.")
                    self.last_error = "Empty message content"
                    self.last_request_succeeded = False
                    return None
                else:
                    logger.warning("Grok API response choices array was empty.")
                    self.last_error = "Empty choices array"
                    self.last_request_succeeded = False
                    return None
            elif response.status_code == 401:
                err_msg = "401 Unauthorized: Invalid API Key."
                logger.error(err_msg)
                self.last_error = err_msg
                self.last_request_succeeded = False
                return None
            elif response.status_code == 429:
                err_msg = "429 Rate Limit Exceeded on Grok API."
                logger.warning(err_msg)
                self.last_error = err_msg
                self.last_request_succeeded = False
                return None
            else:
                err_text = response.text[:140].replace("\n", " ")
                err_msg = f"HTTP {response.status_code}: {err_text}"
                logger.warning(f"Grok API call failed: {err_msg}")
                self.last_error = err_msg
                self.last_request_succeeded = False
                return None

        except requests.exceptions.Timeout:
            err_msg = f"Request timeout after {timeout}s connecting to Grok API."
            logger.warning(err_msg)
            self.last_error = err_msg
            self.last_request_succeeded = False
            return None
        except requests.exceptions.RequestException as e:
            err_msg = f"Network exception during Grok API call: {type(e).__name__}"
            logger.warning(err_msg)
            self.last_error = err_msg
            self.last_request_succeeded = False
            return None
        except Exception as e:
            err_msg = f"Unexpected error during Grok API call: {type(e).__name__}"
            logger.error(err_msg, exc_info=True)
            self.last_error = err_msg
            self.last_request_succeeded = False
            return None

    def _call_chat_completions(self, messages: List[Dict[str, str]], temperature: Optional[float] = None) -> Optional[str]:
        """Wrapper invoking client.chat.completions.create with robust error handling."""
        client = self._get_client()
        if not client:
            return None

        temp = temperature if temperature is not None else self.temperature
        model_name = self.model or os.getenv("GROK_MODEL", "grok-2-latest").strip()

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temp,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            if response and response.choices and len(response.choices) > 0:
                msg = response.choices[0].message
                content = getattr(msg, "content", None)
                if content and content.strip():
                    self.last_request_succeeded = True
                    self.last_error = None
                    return content.strip()
                logger.warning("Grok response content was empty.")
                self.last_request_succeeded = False
                return None
            else:
                logger.warning("Grok response choices were empty.")
                self.last_request_succeeded = False
                return None
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Grok generation failed ({type(e).__name__}): {err_str[:120]}. Falling back safely.")
            self.last_error = err_str[:120]
            self.last_request_succeeded = False
            return None

    def generate_answer(
        self,
        query: str,
        catalog_evidence: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        target_language: str = "en",
        intent: Optional[str] = None,
        clause_status: Optional[str] = None,
        requested_clause: Optional[str] = None,
        ambiguity_guidance: Optional[str] = None
    ) -> Optional[str]:
        """Synthesizes an intelligent, context-aware answer using xAI Grok."""
        lang_instructions = {
            "en": "English",
            "hi": "Hindi (हिन्दी) - Use formal, clear Hindi in Devanagari script, preserving IS codes (e.g. 'IS 4151') intact.",
            "ta": "Tamil (தமிழ்) - Use formal, clear Tamil in Tamil script, preserving IS codes (e.g. 'IS 4151') intact."
        }
        target_lang_desc = lang_instructions.get(target_language, "English")

        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        if conversation_history:
            for turn in conversation_history[-4:]:
                role = turn.get("role")
                content = turn.get("content", "").strip()
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        evidence_block = "No direct catalog record match found in local database. Provide a general, authoritative BIS explanation or procedural guidance."
        if catalog_evidence:
            evidence_summary = {
                "standard_number": catalog_evidence.get("standard_number") or catalog_evidence.get("standard_code"),
                "standard_title": catalog_evidence.get("standard_title") or catalog_evidence.get("title"),
                "product_match_or_scope": catalog_evidence.get("product_match") or catalog_evidence.get("scope"),
                "certification_scheme": catalog_evidence.get("certification_scheme") or catalog_evidence.get("certification_information", {}).get("scheme"),
                "mandatory_status": catalog_evidence.get("mandatory_status") or catalog_evidence.get("certification_information", {}).get("mandatory_status"),
                "testing_parameters": catalog_evidence.get("testing_parameters") or catalog_evidence.get("testing_information"),
                "cataloged_clauses": catalog_evidence.get("page_section_clause") or catalog_evidence.get("reference_clause"),
                "reference_document": catalog_evidence.get("reference_document") or catalog_evidence.get("source_document"),
                "source_url": catalog_evidence.get("source") or catalog_evidence.get("source_url")
            }
            evidence_block = json.dumps({k: v for k, v in evidence_summary.items() if v is not None}, indent=2, ensure_ascii=False)

        clause_note = ""
        if requested_clause:
            if clause_status == "Verified Clause Citation from Catalog Record":
                clause_note = f"\nUser specifically asked about '{requested_clause}'. It is cataloged in the evidence. Address it directly."
            else:
                clause_note = f"\nUser asked about '{requested_clause}', but it is NOT cataloged in available records. You must explicitly clarify that the current catalog summary does not index '{requested_clause}' without claiming it does not exist in the official standard."

        if not catalog_evidence:
            product_words = [
                "mouse", "keyboard", "earphone", "headphone", "monitor", "charger",
                "battery", "cable", "wire", "helmet", "cement", "water", "cooker",
                "light", "lamp", "led", "fan", "heater", "pump", "switch", "socket",
                "toy", "shoe", "footwear", "pipe", "valve", "steel", "glass", "bottle",
                "speaker", "laptop", "mobile", "luminaire", "purifier", "geyser"
            ]
            if intent in ["STANDARD_RECOMMENDATION", "PRODUCT_COMPLIANCE", "BIS_STANDARD_LOOKUP"] or any(w in query.lower() for w in product_words):
                if not ambiguity_guidance:
                    ambiguity_guidance = (
                        "Product inquiry without direct catalog evidence. Do not fabricate or invent Indian Standard numbers (do NOT cite unrelated standards like IS 4151). "
                        "Explain what technical parameters are needed (product type, interface e.g. USB-A/USB-C, power/voltage) to identify applicable BIS requirements, "
                        "explain whether voluntary Scheme I (ISI) or compulsory Scheme II (CRS) applies, explain how to verify on Manakonline (www.manakonline.in), and ask a helpful clarifying question."
                    )

        ambiguity_note = f"\nGUIDANCE FOR THIS QUERY: {ambiguity_guidance}" if ambiguity_guidance else ""
        intent_note = f"\nCLASSIFIED QUERY INTENT: {intent}" if intent else ""

        user_content = f"""USER QUERY: {query}
TARGET LANGUAGE: {target_lang_desc}{intent_note}{clause_note}{ambiguity_note}

AUTHORITATIVE CATALOG EVIDENCE:
{evidence_block}

TASK:
Produce an accurate, helpful answer for the user based on the instructions above."""

        messages.append({"role": "user", "content": user_content})

        return self._call_chat_completions(messages)

    def generate_grounded_answer(
        self,
        query: str,
        catalog_evidence: Dict[str, Any],
        target_language: str = "en",
        clause_status: Optional[str] = None,
        requested_clause: Optional[str] = None
    ) -> Optional[str]:
        """Backward-compatible method for grounded evidence synthesis."""
        return self.generate_answer(
            query=query,
            catalog_evidence=catalog_evidence,
            target_language=target_language,
            clause_status=clause_status,
            requested_clause=requested_clause
        )

    def generate_conversational_answer(
        self,
        query: str,
        target_language: str = "en",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        """Generates a warm, professional conversational response (e.g. greeting, pleasantry)."""
        lang_instructions = {
            "en": "English",
            "hi": "Hindi (हिन्दी)",
            "ta": "Tamil (தமிழ்)"
        }
        target_lang_desc = lang_instructions.get(target_language, "English")

        system_prompt = (
            "You are BIS-AI, an intelligent conversational assistant dedicated to Indian Standards "
            "and Bureau of Indian Standards (BIS) services. You are warm, polite, professional, and helpful. "
            f"Respond concisely to the greeting or conversational message in {target_lang_desc}."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for turn in conversation_history[-3:]:
                if turn.get("role") in ("user", "assistant") and turn.get("content"):
                    messages.append(turn)
        messages.append({"role": "user", "content": query})

        return self._call_chat_completions(messages, temperature=0.7)

    def generate_knowledge_answer(
        self,
        query: str,
        target_language: str = "en",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        """Answers general educational, science, or technology questions clearly."""
        lang_instructions = {
            "en": "English",
            "hi": "Hindi (हिन्दी)",
            "ta": "Tamil (தமிழ்)"
        }
        target_lang_desc = lang_instructions.get(target_language, "English")

        system_prompt = (
            "You are BIS-AI, an intelligent assistant. The user is asking a general educational, "
            "scientific, or technical question. Provide a clear, accurate, and concise answer in "
            f"{target_lang_desc}. Conclude with a brief polite note that you can also assist with any Indian "
            "Standards or BIS compliance requirements."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for turn in conversation_history[-3:]:
                if turn.get("role") in ("user", "assistant") and turn.get("content"):
                    messages.append(turn)
        messages.append({"role": "user", "content": query})

        return self._call_chat_completions(messages, temperature=0.5)

    def generate_clarification(
        self,
        query: str,
        target_language: str = "en",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        """Generates a targeted clarifying question when the user's query is brief or ambiguous."""
        lang_instructions = {
            "en": "English",
            "hi": "Hindi (हिन्दी)",
            "ta": "Tamil (தமிழ்)"
        }
        target_lang_desc = lang_instructions.get(target_language, "English")

        system_prompt = (
            "You are BIS-AI, an assistant for Indian Standards and BIS services. The user's query is very "
            f"brief or ambiguous. Ask a polite, concise clarifying question in {target_lang_desc} to help them "
            "specify the product, standard number, or BIS scheme they are looking for."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for turn in conversation_history[-3:]:
                if turn.get("role") in ("user", "assistant") and turn.get("content"):
                    messages.append(turn)
        messages.append({"role": "user", "content": query})

        return self._call_chat_completions(messages, temperature=0.4)


# Global singleton instance
grok_service = GrokService()
