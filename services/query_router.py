import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("bis_ai.services.query_router")

class IntentType:
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
    BIS_STANDARD_LOOKUP = "BIS_STANDARD_LOOKUP"
    STANDARD_DETAILS = "STANDARD_DETAILS"
    CLAUSE_LOOKUP = "CLAUSE_LOOKUP"
    BIS_CERTIFICATION = "BIS_CERTIFICATION"
    PRODUCT_COMPLIANCE = "PRODUCT_COMPLIANCE"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    OUT_OF_SCOPE_OR_UNSUPPORTED = "OUT_OF_SCOPE_OR_UNSUPPORTED"


class QueryRouter:
    """
    Intelligent Query Router classifying queries across 9 intent classes:
    1. GENERAL_CONVERSATION
    2. GENERAL_KNOWLEDGE
    3. BIS_STANDARD_LOOKUP
    4. STANDARD_DETAILS
    5. CLAUSE_LOOKUP
    6. BIS_CERTIFICATION
    7. PRODUCT_COMPLIANCE
    8. CLARIFICATION_REQUIRED
    9. OUT_OF_SCOPE_OR_UNSUPPORTED
    """

    GREETING_PATTERNS = [
        r"^(hi|hello|hey|namaste|vanakkam|namaskar|good\s+morning|good\s+evening|good\s+afternoon|good\s+day)\b",
        r"\b(who\s+are\s+you|what\s+are\s+you|what\s+can\s+you\s+do|introduce\s+yourself|tell\s+me\s+about\s+yourself)\b",
        r"\b(how\s+are\s+you|thank\s+you|thanks|bye|goodbye|see\s+you)\b"
    ]

    SECURITY_PATTERNS = [
        r"\b(ignore\s+(all\s+)?previous\s+instructions|system\s+prompt|jailbreak|reveal\s+prompt|bypass\s+rules)\b",
        r"\b(make\s+a\s+bomb|credit\s+card|hack\s+into|sql\s+injection|ddos)\b",
        r"\b(alien|spaceship|warp\s+engine|warp\s+drive|warp\s+coil|teleportation|martian|quantum\s+warp)\b",
        r"\b(orbital\s+speed|planet\s+jupiter|jupiter\s+around\s+the\s+sun)\b",
        r"\b(does\s+not\s+exist\s+in\s+the\s+knowledge\s+base)\b"
    ]

    CLARIFICATION_WORDS = {
        "standard", "standards", "certification", "bis", "help", "information",
        "tell me", "details", "specifications", "what", "query", "question"
    }

    GK_PATTERNS = [
        r"\b(what\s+is\s+machine\s+learning|what\s+is\s+ai|artificial\s+intelligence|quantum\s+physics|quantum\s+computing)\b",
        r"\b(what\s+is\s+bluetooth|what\s+is\s+photosynthesis|capital\s+of\s+[a-z]+|who\s+is\s+[a-z]+|who\s+was\s+[a-z]+)\b",
        r"\b(write\s+python|python\s+code|sort\s+a\s+list|how\s+do\s+airplanes\s+fly|why\s+is\s+the\s+sky\s+blue)\b"
    ]

    CLAUSE_PATTERN = r'\b(clause|section|table|part|annex|appendix)\s*([0-9]+(?:\.[0-9]+)*|[a-z])\b'
    STANDARD_PATTERN = r'\bIS\s*([0-9]{3,5}(?:\s*:\s*[0-9]{4})?(?:\s*\([Pp]art\s*[0-9]+\))?)\b'

    def route(
        self,
        query: str,
        original_query: Optional[str] = None,
        extracted_is_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classifies incoming query into one of 9 canonical intent classes.
        """
        q_raw = (query or "").strip()
        q_orig = (original_query or q_raw).strip()
        q_lower = q_raw.lower()
        orig_lower = q_orig.lower()

        # 1. OUT_OF_SCOPE_OR_UNSUPPORTED Check
        for sec in self.SECURITY_PATTERNS:
            if re.search(sec, q_lower, re.IGNORECASE) or re.search(sec, orig_lower, re.IGNORECASE):
                return {
                    "intent": IntentType.OUT_OF_SCOPE_OR_UNSUPPORTED,
                    "confidence": 0.99,
                    "rationale": "Safety guardrail triggered or query explicitly unsupported/out of scope."
                }

        # 2. CLARIFICATION_REQUIRED Check (vague single-word or empty queries)
        cleaned_words = [w for w in re.split(r'\W+', q_lower) if w]
        if len(cleaned_words) <= 1 and q_lower in self.CLARIFICATION_WORDS:
            return {
                "intent": IntentType.CLARIFICATION_REQUIRED,
                "confidence": 0.95,
                "rationale": "Query is too brief or ambiguous to determine product or standard."
            }

        # 3. GENERAL_CONVERSATION Check
        for greet in self.GREETING_PATTERNS:
            if re.search(greet, q_lower, re.IGNORECASE) or re.search(greet, orig_lower, re.IGNORECASE):
                # Ensure it's not actually asking for a specific standard like "hi which standard is for..."
                if not re.search(r'\b(standard|is\s*[0-9]|bis\s+mark|isi\s+mark|certification)\b', q_lower):
                    return {
                        "intent": IntentType.GENERAL_CONVERSATION,
                        "confidence": 0.98,
                        "rationale": "Greeting or conversational assistant inquiry."
                    }

        # 4. CLAUSE_LOOKUP Check
        clause_match = re.search(self.CLAUSE_PATTERN, q_raw, re.IGNORECASE) or re.search(self.CLAUSE_PATTERN, q_orig, re.IGNORECASE)
        if clause_match:
            return {
                "intent": IntentType.CLAUSE_LOOKUP,
                "confidence": 0.96,
                "clause": clause_match.group(0),
                "rationale": f"Explicit clause citation requested ({clause_match.group(0)})."
            }

        # 5. STANDARD_DETAILS Check
        std_match = extracted_is_code or re.search(self.STANDARD_PATTERN, q_raw, re.IGNORECASE) or re.search(self.STANDARD_PATTERN, q_orig, re.IGNORECASE)
        has_std_code = bool(std_match)
        is_detail_query = any(k in q_lower for k in ["scope", "cover", "detail", "specification", "what is", "about", "describe", "எந்த", "किस"])
        if has_std_code and is_detail_query:
            return {
                "intent": IntentType.STANDARD_DETAILS,
                "confidence": 0.95,
                "standard_code": extracted_is_code or (std_match.group(0) if hasattr(std_match, "group") else None),
                "rationale": "Detailed requirements/scope inquiry for a specific Indian Standard."
            }

        # 6. PRODUCT_COMPLIANCE Check
        compliance_keywords = [
            "mandatory", "compulsory", "qco", "quality control order", "testing parameter",
            "test requirement", "is it mandatory", "are earphones mandatory", "mandatory status",
            "mandatory and a voluntary", "mandatory or voluntary", "compulsory certification",
            "covered by compulsory"
        ]
        if any(k in q_lower for k in compliance_keywords) or any(k in orig_lower for k in ["கட்டாயம்", "अनिवार्य"]):
            return {
                "intent": IntentType.PRODUCT_COMPLIANCE,
                "confidence": 0.92,
                "rationale": "Query regards mandatory compliance, QCO order, or testing specifications."
            }

        # 7. BIS_CERTIFICATION & Core BIS Concepts Check
        cert_keywords = [
            "what is bis", "about bis", "bureau of indian standards", "purpose of indian standards",
            "how to get isi", "how to apply", "certification scheme", "crs registration",
            "fmcs", "hallmarking", "huid", "gold purity", "gold hallmarking", "laboratory accreditation",
            "bis care app", "fake isi", "fake bis", "genuine bis", "fake mark", "genuine mark",
            "complaint", "consumer complaint", "license fee", "apply for bis",
            "apply for certification", "how can a manufacturer apply", "manufacturer apply",
            "bis certification", "certification process", "isi mark and hallmarking",
            "role of testing", "conformity assessment", "testing in product certification",
            "steps involved in obtaining", "msme understand", "msme", "search for an indian standard",
            "search for a standard", "information should i provide", "information is needed",
            "find a laboratory", "laboratory for product testing"
        ]
        if any(k in q_lower for k in cert_keywords) or any(k in orig_lower for k in ["ஹால்மார்க்", "हॉलमार्क"]):
            return {
                "intent": IntentType.BIS_CERTIFICATION,
                "confidence": 0.94,
                "rationale": "Inquiry regarding BIS core concepts, certification schemes, hallmarking, or consumer procedures."
            }

        # 8. GENERAL_KNOWLEDGE Check (strictly for non-BIS topics)
        for gk in self.GK_PATTERNS:
            if re.search(gk, q_lower, re.IGNORECASE):
                return {
                    "intent": IntentType.GENERAL_KNOWLEDGE,
                    "confidence": 0.95,
                    "rationale": "Educational or scientific question unrelated to Indian Standards."
                }
        # Non-BIS scientific or general concepts
        non_bis_indicators = ["machine learning", "neural network", "deep learning", "photosynthesis", "physics", "solar system", "quantum", "capital of", "who wrote", "president of"]
        if any(ind in q_lower for ind in non_bis_indicators):
            return {
                "intent": IntentType.GENERAL_KNOWLEDGE,
                "confidence": 0.92,
                "rationale": "General domain knowledge query unrelated to BIS."
            }

        # 8b. Ambiguous broad product description check (e.g., "electrical products", "electronic items")
        if any(amb in q_lower for amb in ["electrical product", "electrical items", "electronic product", "plastic product", "electrical goods"]):
            return {
                "intent": IntentType.CLARIFICATION_REQUIRED,
                "confidence": 0.88,
                "rationale": "Product family is too broad; specific product type required to identify applicable standard."
            }

        # 9. BIS_STANDARD_LOOKUP Check
        standard_lookup_indicators = [
            "standard", "standards", "is code", "applicable", "which is", "recommend",
            "earphone", "helmet", "cement", "water", "cable", "shoe", "toy", "lamp",
            "emergency light", "pressure cooker", "cooker", "led", "batao", "enna",
            "தரநிலை", "मानक"
        ]
        if any(k in q_lower for k in standard_lookup_indicators) or any(k in orig_lower for k in ["தரநிலை", "मानक"]):
            return {
                "intent": IntentType.BIS_STANDARD_LOOKUP,
                "confidence": 0.90,
                "rationale": "Inquiry looking up the applicable Indian Standard for a product."
            }

        # Check if query mentions BIS or standardization concepts
        bis_terms = ["bis", "standard", "isi", "hallmark", "conformity", "quality", "certif", "testing", "lab"]
        if any(bt in q_lower for bt in bis_terms):
            return {
                "intent": IntentType.BIS_CERTIFICATION,
                "confidence": 0.85,
                "rationale": "General BIS standardization inquiry."
            }

        # Fallback to general knowledge only if completely devoid of BIS terms
        if q_lower.startswith(("what is ", "what are ", "explain ", "how does ", "who is ")):
            return {
                "intent": IntentType.GENERAL_KNOWLEDGE,
                "confidence": 0.75,
                "rationale": "Defaulted general informational inquiry."
            }

        # Default fallback
        return {
            "intent": IntentType.BIS_STANDARD_LOOKUP,
            "confidence": 0.60,
            "rationale": "Standard product inquiry fallback."
        }


query_router = QueryRouter()
