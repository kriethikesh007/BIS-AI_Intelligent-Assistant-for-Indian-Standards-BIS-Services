import logging
from typing import Dict, Any, List
from config import Config
from services.multilingual import MultilingualService
from ml.classifier_service import intent_classifier
from retrieval.retriever import retriever
from database.db import db_manager

logger = logging.getLogger("bis_ai.orchestrator")

FALLBACK_MESSAGE = "Reliable BIS information could not be found for this query."

class AssistantOrchestrator:
    """
    Coordinates the end-to-end question answering and recommendation pipeline:
    1. Multilingual processing & language identification.
    2. Intent classification via Voting Ensemble (RF + Extra Trees + Gradient Boosting).
    3. Hybrid retrieval across standards, schemes, labs, and consumer procedures.
    4. Guardrails: Source-backed strict validation - Never invent standards.
    5. Formulates structured output containing:
       - Answer
       - Recommended standard/service if applicable
       - Reason
       - Source
       - Reference document
       - Page/section/clause when available
       - Confidence score
    6. Multilingual localization when needed.
    """

    def process_user_query(self, query: str) -> Dict[str, Any]:
        if not query or not query.strip():
            return {
                "answer": "Please provide a query regarding Indian Standards or BIS services.",
                "confidence_score": 0.0,
                "recommended_standard": None,
                "reason": "Empty query",
                "source": "BIS-AI Gateway",
                "reference_document": None,
                "page_section_clause": None,
                "intent": "OTHER",
                "detected_language": "en"
            }

        # 1. Multilingual Processing & Language Detection
        multi_info = MultilingualService.process_query(query)
        detected_lang = multi_info["detected_language"]
        processed_query = multi_info["processed_query"]
        answer_lang = multi_info["answer_language"]

        # 2. Ensemble Intent Classification (on processed English query)
        pred_intent, intent_confidence, prob_dist = intent_classifier.predict(processed_query)

        # 3. Domain Dispatch & Evidence Retrieval
        response_payload = self._dispatch_intent(processed_query, pred_intent, intent_confidence)

        # 4. Translate response back to user's language
        if answer_lang in ["hi", "ta"]:
            response_payload["answer"] = MultilingualService.translate_answer(
                response_payload["answer"], answer_lang
            )

        # Attach multilingual metadata
        response_payload["original_query"] = query
        response_payload["detected_language"] = detected_lang
        response_payload["processed_query"] = processed_query
        response_payload["answer_language"] = answer_lang
        response_payload["translated_query"] = processed_query if detected_lang != "en" else None
        response_payload["intent_distribution"] = prob_dist

        # Log query to database
        db_manager.log_query({
            "original_query": query,
            "detected_lang": detected_lang,
            "processed_query": processed_query,
            "answer_language": answer_lang,
            "intent": pred_intent,
            "confidence": response_payload.get("confidence_score", 0.0),
            "recommended_standard": response_payload.get("recommended_standard")
        })

        return response_payload

    def _dispatch_intent(self, query: str, intent: str, intent_conf: float) -> Dict[str, Any]:
        # Handle non-BIS or greeting queries cleanly
        if intent == "OTHER":
            return {
                "answer": "I am BIS-AI, an intelligent conversational assistant dedicated to Indian Standards and Bureau of Indian Standards (BIS) services. How can I assist you with standard specifications, product certification, hallmarking, or testing labs?",
                "recommended_standard": None,
                "reason": "Query outside BIS standardization scope.",
                "source": "BIS-AI Knowledge Portal",
                "reference_document": "BIS Citizen Charter",
                "page_section_clause": "Preamble",
                "confidence_score": round(intent_conf, 2),
                "intent": intent
            }

        # 1. Standard Recommendation or Standard Information
        if intent in ["STANDARD_RECOMMENDATION", "STANDARD_INFORMATION"]:
            standards = retriever.search_and_recommend(query, top_k=2)
            if not standards:
                return {
                    "answer": FALLBACK_MESSAGE,
                    "recommended_standard": None,
                    "reason": "No certified standard matched product specification in current BIS database.",
                    "source": "Bureau of Indian Standards",
                    "reference_document": None,
                    "page_section_clause": None,
                    "confidence_score": 0.0,
                    "intent": intent
                }
            top_std = standards[0]
            action_desc = "Applicable Indian Standard identified" if intent == "STANDARD_RECOMMENDATION" else "Standard Details & Scope"
            ans_text = (
                f"**{top_std['standard_code']} - {top_std['title']}**\n\n"
                f"• **Scope & Technical Requirements:** {top_std['scope']}\n"
                f"• **Certification Scheme:** {top_std['certification_scheme']} ({top_std['mandatory_status']})\n"
                f"• **Key Testing Parameters:** {top_std['testing_parameters']}"
            )
            return {
                "answer": ans_text,
                "recommended_standard": top_std["standard_code"],
                "reason": f"Product matches '{top_std['category']}' category for {top_std['product']} via {top_std.get('match_type', 'Hybrid Match')}.",
                "source": top_std["source_url"],
                "reference_document": top_std["source_document"],
                "page_section_clause": top_std["reference_clause"],
                "confidence_score": round(top_std["relevance_score"], 2),
                "intent": intent,
                "additional_matches": [
                    {"code": s["standard_code"], "title": s["title"], "score": s["relevance_score"]}
                    for s in standards[1:]
                ]
            }

        # 2. Certification Schemes and Procedures
        if intent == "CERTIFICATION":
            schemes = retriever.search_schemes(query)
            if schemes:
                top_sch = schemes[0]
                ans_text = (
                    f"**{top_sch['scheme_name']}**\n\n"
                    f"• **Description:** {top_sch['description']}\n\n"
                    f"• **Step-by-Step Procedure:**\n{top_sch['procedure']}\n\n"
                    f"• **MSME / Startup Benefits:** {top_sch.get('concessions_msme_startups', 'Standard guidelines apply.')}"
                )
                return {
                    "answer": ans_text,
                    "recommended_standard": top_sch["scheme_name"],
                    "reason": "Query requests procedure and criteria for BIS certification schemes.",
                    "source": top_sch["source_url"],
                    "reference_document": top_sch["source_document"],
                    "page_section_clause": top_sch["reference_clause"],
                    "confidence_score": round(top_sch["relevance_score"], 2),
                    "intent": intent
                }

        # 3. Hallmarking & HUID
        if intent == "HALLMARKING":
            faqs = retriever.search_faqs(query)
            hallmark_faq = next((f for f in faqs if "hallmarking" in f.get("topic", "").lower() or "huid" in f.get("topic", "").lower()), None)
            if hallmark_faq:
                return {
                    "answer": hallmark_faq["answer"],
                    "recommended_standard": "IS 1417 (Gold) / IS 2112 (Silver)",
                    "reason": "Precious metals hallmarking and HUID verification guidelines under BIS Act 2016.",
                    "source": hallmark_faq["source_url"],
                    "reference_document": hallmark_faq["source_document"],
                    "page_section_clause": hallmark_faq["reference_clause"],
                    "confidence_score": round(hallmark_faq["relevance_score"], 2),
                    "intent": intent
                }
            # Fallback to standards
            standards = retriever.search_and_recommend("gold jewellery hallmarking", top_k=1)
            if standards:
                s = standards[0]
                return {
                    "answer": f"**Gold & Silver Hallmarking:** Governed by {s['standard_code']}: {s['title']}. {s['scope']}",
                    "recommended_standard": s["standard_code"],
                    "reason": "Authorized standard for gold and silver jewellery hallmarking.",
                    "source": s["source_url"],
                    "reference_document": s["source_document"],
                    "page_section_clause": s["reference_clause"],
                    "confidence_score": round(s["relevance_score"], 2),
                    "intent": intent
                }

        # 4. Testing Laboratories
        if intent == "LABORATORY":
            labs = retriever.search_laboratories(query)
            if labs:
                top_lab = labs[0]
                ans_text = (
                    f"**Recommended Laboratory: {top_lab['lab_name']}**\n\n"
                    f"• **Type & Accreditation:** {top_lab['type']} ({top_lab['accreditation']})\n"
                    f"• **Location:** {top_lab['city']}, {top_lab['state']} ({top_lab['address']})\n"
                    f"• **Disciplines:** {', '.join(top_lab['disciplines'])}\n"
                    f"• **Tested Products:** {', '.join(top_lab['tested_products'])}\n"
                    f"• **Contact:** {top_lab['contact']}"
                )
                return {
                    "answer": ans_text,
                    "recommended_standard": f"Lab Accreditation: {top_lab['accreditation']}",
                    "reason": f"Laboratory equipped with testing infrastructure for specified disciplines in {top_lab['city']}.",
                    "source": top_lab["source_url"],
                    "reference_document": top_lab["source_document"],
                    "page_section_clause": top_lab["reference_clause"],
                    "confidence_score": round(top_lab["relevance_score"], 2),
                    "intent": intent,
                    "laboratories_found": labs[:3]
                }

        # 5. Consumer & Grievances
        if intent in ["CONSUMER", "GENERAL_BIS"]:
            faqs = retriever.search_faqs(query)
            if faqs:
                top_faq = faqs[0]
                return {
                    "answer": top_faq["answer"],
                    "recommended_standard": "BIS CARE Mobile App & Manakonline Portal",
                    "reason": f"Official consumer guidance for {top_faq['topic']}.",
                    "source": top_faq["source_url"],
                    "reference_document": top_faq["source_document"],
                    "page_section_clause": top_faq["reference_clause"],
                    "confidence_score": round(top_faq["relevance_score"], 2),
                    "intent": intent
                }

        # Global fallthrough search across all collections
        stds = retriever.search_and_recommend(query, top_k=1)
        if stds and stds[0]["relevance_score"] >= Config.RELEVANCE_THRESHOLD:
            s = stds[0]
            return {
                "answer": f"**Applicable Standard:** {s['standard_code']} - {s['title']}\n\n{s['scope']}",
                "recommended_standard": s["standard_code"],
                "reason": f"Matched keywords in product specification: {s['product']}",
                "source": s["source_url"],
                "reference_document": s["source_document"],
                "page_section_clause": s["reference_clause"],
                "confidence_score": round(s["relevance_score"], 2),
                "intent": intent
            }

        return {
            "answer": FALLBACK_MESSAGE,
            "recommended_standard": None,
            "reason": "Evidence not sufficient to provide authoritative BIS guidance.",
            "source": "Bureau of Indian Standards Official Portal",
            "reference_document": None,
            "page_section_clause": None,
            "confidence_score": 0.0,
            "intent": intent
        }

orchestrator = AssistantOrchestrator()
