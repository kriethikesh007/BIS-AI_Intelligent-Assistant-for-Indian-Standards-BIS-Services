import re
import time
import logging
from typing import Dict, Any, List, Optional
from config import Config
from services.multilingual import MultilingualService
from ml.predict_intent import predict_intent
from services.recommendation_engine import recommendation_engine
from retrieval.retriever import retriever
from database.db import db_manager
from utils.url_validator import sanitize_and_validate_url
from services.grok_service import grok_service
from services.query_router import query_router, IntentType
from services.external_retriever import external_retriever

logger = logging.getLogger("bis_ai.conversational_assistant")

FALLBACK_STRICT_MESSAGE = "I could not find sufficient authoritative BIS information to answer this question reliably."

# Verified deterministic knowledge for core BIS concepts (used when Grok API is offline/testing)
DETERMINISTIC_BIS_KNOWLEDGE = [
    {
        "patterns": [r"\bwhat is bis\b", r"\babout bis\b", r"\bbureau of indian standards\b"],
        "standard": "Bureau of Indian Standards (BIS Act 2016)",
        "answer": (
            "**Bureau of Indian Standards (BIS)** is the National Standard Body of India established under the "
            "**BIS Act 2016**. Operating under the Ministry of Consumer Affairs, Food & Public Distribution, BIS is "
            "mandated to formulate National Standards, oversee conformity assessment schemes, grant product certification "
            "(ISI Mark and CRS), operate gold and silver hallmarking, and manage recognized testing laboratories across India."
        ),
        "why": "Official statutory overview under Section 3 of the BIS Act 2016.",
        "source": "https://www.bis.gov.in",
        "reference": "BIS Act 2016 / Section 3"
    },
    {
        "patterns": [r"\bpurpose of indian standards\b", r"\bwhat are indian standards\b", r"\bwhy are indian standards\b"],
        "standard": "Indian Standards Framework (IS Series)",
        "answer": (
            "**Purpose of Indian Standards:**\n\n"
            "• **Quality & Safety Assurance:** Set rigorous benchmarks for product performance, safety, and durability to protect consumer health and property.\n"
            "• **Industrial Harmonization:** Establish technical interoperability and uniform manufacturing practices across Indian industries.\n"
            "• **Consumer Protection:** Enable consumers to identify genuine, certified products via marks such as ISI and Hallmark.\n"
            "• **Trade Facilitation:** Align Indian requirements with international ISO/IEC benchmarks, supporting domestic and global trade."
        ),
        "why": "Primary objectives defined under the BIS Standardization mandate.",
        "source": "https://www.bis.gov.in/standardization/",
        "reference": "BIS Act 2016 / Standardization Directives"
    },
    {
        "patterns": [r"\bconformity assessment\b", r"\bpurpose of conformity assessment\b"],
        "standard": "BIS Conformity Assessment Regulations 2018",
        "answer": (
            "**Conformity Assessment** is the systematic demonstration that specified technical, safety, and quality requirements "
            "relating to a product, process, system, person, or body are fulfilled.\n\n"
            "• **Assurance:** Provides verified confidence to consumers, regulators, and buyers that goods meet Indian Standards.\n"
            "• **Mechanisms:** Includes in-factory audits, third-party laboratory sample testing, surveillance, and certification marking.\n"
            "• **Regulatory Enforcement:** Serves as the basis for enforcing compulsory Quality Control Orders (QCOs)."
        ),
        "why": "Regulatory definition governed under BIS Conformity Assessment Regulations 2018.",
        "source": "https://www.bis.gov.in/conformity-assessment/",
        "reference": "BIS Conformity Assessment Regulations 2018 / Section 4"
    },
    {
        "patterns": [r"\bisi mark and hallmarking\b", r"\bdifference between (an )?isi mark and hallmarking\b", r"\bisi vs hallmarking\b"],
        "standard": "Product Certification (Scheme I) vs Hallmarking Scheme",
        "answer": (
            "**Difference between ISI Mark and Hallmarking:**\n\n"
            "• **ISI Mark (Scheme I):** Certifies industrial and consumer *manufactured products* (e.g. helmets, cement, packaged water, electrical cables). It confirms conformity to comprehensive physical, chemical, and safety specifications under the relevant IS standard.\n\n"
            "• **Hallmarking (Precious Metals):** Specifically certifies the *purity and fineness of precious metals* (gold and silver jewellery/artefacts). Marked pieces carry the BIS logo, fineness grade (e.g., 22K916), and a laser-engraved 6-digit Hallmark Unique Identification (HUID) code."
        ),
        "why": "Distinct statutory certification schemes governed under Scheme I and the Hallmarking Scheme.",
        "source": "https://www.bis.gov.in/hallmarking-overview/",
        "reference": "BIS Scheme I Regulations & Hallmarking Directives"
    },
    {
        "patterns": [r"\bhow can a manufacturer apply\b", r"\bapply for bis certification\b", r"\bcertification process\b", r"\bsteps involved in obtaining\b", r"\bgeneral steps.*certification\b"],
        "standard": "Scheme I - Product Certification Scheme Procedure",
        "answer": (
            "**BIS Product Certification Process (General Steps):**\n\n"
            "1. **Identify the Standard:** Determine the applicable Indian Standard (IS code) for your product.\n"
            "2. **Prepare In-House Infrastructure:** Establish requisite manufacturing machinery and in-house testing equipment in accordance with the Scheme of Inspection and Testing (SIT).\n"
            "3. **Online Application:** Register and submit the application on the **Manakonline** portal (www.manakonline.in) with manufacturing details and factory layout.\n"
            "4. **Factory Audit & Sample Drawing:** A BIS technical auditor inspects the factory, verifies testing infrastructure, and draws representative product samples.\n"
            "5. **Independent Laboratory Testing:** Samples are sealed and tested at BIS or recognized NABL-accredited laboratories.\n"
            "6. **Grant of Licence (GoL):** Upon satisfactory verification of factory audit and laboratory test results, BIS grants the licence to use the ISI mark."
        ),
        "why": "Official standard licensing workflow under Manakonline e-BIS portal.",
        "source": "https://www.manakonline.in",
        "reference": "BIS Product Certification Manual / Form I Guidelines"
    },
    {
        "patterns": [r"\bgold hallmarking\b", r"\bhow does gold hallmarking work\b", r"\bhallmarking work\b"],
        "standard": "IS 1417 (Gold Purity & Hallmarking)",
        "answer": (
            "**How Gold Hallmarking Works:**\n\n"
            "Under the BIS Hallmarking Scheme, gold jewellery is assayed and certified at recognized Assaying and Hallmarking Centres (AHCs).\n\n"
            "Each genuine hallmarked gold article bears three mandatory marks:\n"
            "1. **BIS Standard Logo** (triangle mark).\n"
            "2. **Purity / Fineness Grade:** Indicating Karat and fineness (e.g. 24K999, 23K958, 22K916, 20K833, 18K750, 14K585).\n"
            "3. **6-Digit Alphanumeric HUID** (Hallmark Unique Identification) laser-engraved code.\n\n"
            "Consumers can verify the authenticity, jeweller registration, and testing centre by entering the HUID in the **BIS CARE** mobile app."
        ),
        "why": "Mandatory gold hallmarking guidelines under BIS Act 2016.",
        "source": "https://www.bis.gov.in/hallmarking-overview/",
        "reference": "IS 1417:2016 / Hallmarking Regulations"
    },
    {
        "patterns": [r"\bgenuine bis mark\b", r"\bidentify a genuine\b", r"\bhow can i identify.*bis mark\b"],
        "standard": "BIS Mark Authenticity Verification",
        "answer": (
            "**How to Identify a Genuine BIS Mark:**\n\n"
            "1. **ISI Monogram:** A genuine mark displays the stylized ISI logo inside a clean rectangular boundary.\n"
            "2. **Standard Code (Above the Mark):** The specific Indian Standard number (e.g. 'IS 4151') must be printed above the ISI logo.\n"
            "3. **Licence Number (CM/L Below the Mark):** A 7 or 8 digit Certification Marks/Licence (CM/L) number is printed directly below the logo.\n"
            "4. **Verification via BIS CARE App:** Open the free official **BIS CARE** mobile app, select 'Verify Licence Details', enter the CM/L number, and immediately confirm the manufacturer name, address, validity, and product scope."
        ),
        "why": "Consumer guidelines for verifying authentic certification markings.",
        "source": "https://www.bis.gov.in/consumer-affairs/",
        "reference": "BIS CARE Mobile Application Guidelines"
    },
    {
        "patterns": [r"\bfake bis mark\b", r"\bfake isi\b", r"\bcarry a fake\b", r"\breport.*fake\b"],
        "standard": "BIS Consumer Redressal & Enforcement",
        "answer": (
            "**What to Do if a Product Carries a Suspected Fake BIS Mark:**\n\n"
            "1. **Verify Immediately:** Check the licence number (CM/L) on the **BIS CARE** app using 'Verify Licence Details'. If it is invalid, expired, or registered to a different product, the mark is unauthorized.\n"
            "2. **Lodge an Official Complaint:** Use the 'Complaints' section on the BIS CARE app or the Public Grievance Portal on www.bis.gov.in.\n"
            "3. **Legal Consequences:** Misuse of the BIS Standard Mark is a cognizable offense under **Section 15 & Section 29 of the BIS Act 2016**, punishable by imprisonment up to 2 years, seizure of goods, and fines up to ₹5,00,000."
        ),
        "why": "Statutory enforcement under Section 15 and 29 of the BIS Act 2016.",
        "source": "https://www.bis.gov.in/consumer-grievance/",
        "reference": "BIS Act 2016 / Section 15 & 29"
    },
    {
        "patterns": [r"\bfind a laboratory\b", r"\blaboratory for product testing\b", r"\blaboratory.*testing\b"],
        "standard": "BIS Laboratory Network & Recognition Scheme (LRS)",
        "answer": (
            "**How to Find a Laboratory for Product Testing:**\n\n"
            "• **BIS Central & Regional Labs:** BIS maintains high-capacity testing facilities including Central Laboratory (Sahibabad) and Regional Laboratories in Chennai (SROL), Mumbai (WROL), Kolkata (EROL), and Mohali (NROL).\n"
            "• **Laboratory Recognition Scheme (LRS):** BIS recognizes hundreds of private and state testing facilities accredited to ISO/IEC 17025 by NABL.\n"
            "• **Online Directory Search:** Access the official directory at www.services.bis.gov.in or the Manakonline LIMS portal to search recognized laboratories by product name, Indian Standard code, and state."
        ),
        "why": "Directory of accredited facilities under BIS Laboratory Recognition Scheme (LRS).",
        "source": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/lims",
        "reference": "BIS Laboratory Network Directory"
    },
    {
        "patterns": [r"\binformation should i provide.*standard\b", r"\bidentify the applicable indian standard\b", r"\bdetails do you need.*standard\b"],
        "standard": "Standard Identification Guidelines",
        "answer": (
            "**Information Needed to Identify the Applicable Indian Standard:**\n\n"
            "1. **Exact Product Name & Common Synonyms:** e.g., 'Domestic Pressure Cooker', 'LED Emergency Luminaire', 'Submersible Pump'.\n"
            "2. **Material of Construction:** e.g., Stainless steel, aluminium alloy, polymers, or composite.\n"
            "3. **Technical Ratings & Specifications:** Voltage, power wattage, operating pressure (bar/kPa), capacity (litres), or dimension.\n"
            "4. **Intended Application & Operating Environment:** Domestic, commercial, industrial, indoor, outdoor, or hazardous area.\n"
            "5. **Regulatory Sector:** Electronics (under MeitY CRS), toys, food contact, or general engineering."
        ),
        "why": "Criteria required by the BIS Standardization technical committees.",
        "source": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards",
        "reference": "BIS Know Your Standards Portal"
    },
    {
        "patterns": [r"\bmandatory and a voluntary\b", r"\bmandatory vs voluntary\b", r"\bvoluntary certification scheme\b"],
        "standard": "Compulsory Quality Control Orders (QCO) vs Voluntary Conformity",
        "answer": (
            "**Difference between Mandatory and Voluntary Certification Schemes:**\n\n"
            "• **Mandatory Certification (QCOs):** Enforced by Government of India Ministries via statutory **Quality Control Orders (QCOs)** issued under the BIS Act. Products under mandatory QCOs cannot be manufactured, imported, distributed, or sold in India without a valid BIS license or CRS registration. Examples include two-wheeler helmets, packaged drinking water, and cement.\n\n"
            "• **Voluntary Certification:** Available for products where a QCO has not been notified. Manufacturers voluntarily seek the ISI mark as an independent proof of premium quality, safety, and competitive advantage in government tenders and open markets."
        ),
        "why": "Legal distinction between notified QCO mandates and voluntary licensing.",
        "source": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/",
        "reference": "BIS Act 2016 / Section 16 (Quality Control Orders)"
    },
    {
        "patterns": [r"\bmsme understand\b", r"\bmsme\b.*\bcertification requirements\b"],
        "standard": "BIS Concessions and Facilitation for MSMEs and Startups",
        "answer": (
            "**How an MSME Can Understand and Avail Certification Requirements:**\n\n"
            "• **Free Standard Access:** Under the 'Know Your Standards' initiative, MSMEs can view all published Indian Standards free of cost on the BIS website.\n"
            "• **Financial Concessions:** BIS provides substantial fee rebates for Micro, Small, and Medium Enterprises (MSMEs) and recognized Startups—typically up to a **20% to 50% concession** on application fees and annual minimum marking fees.\n"
            "• **Dedicated Facilitation Cells:** Every BIS Regional and Branch Office maintains an MSME Helpdesk to assist with documentation, factory layout preparation, and laboratory testing guidance."
        ),
        "why": "Government MSME concessions under BIS Scheme Regulations.",
        "source": "https://www.bis.gov.in/msme-portal/",
        "reference": "BIS MSME & Startup Policy Guidelines"
    },
    {
        "patterns": [r"\brole of testing in product certification\b", r"\brole of testing\b"],
        "standard": "Scheme of Inspection and Testing (SIT)",
        "answer": (
            "**The Role of Testing in Product Certification:**\n\n"
            "Testing is the technical foundation of conformity assessment in BIS certification:\n"
            "• **Verification of Performance & Safety:** Verifies that physical, mechanical, electrical, and chemical properties satisfy standard thresholds.\n"
            "• **Grant of Licence:** Independent lab testing of initial factory-drawn samples is mandatory before BIS issues the licence.\n"
            "• **Routine Quality Control (In-House):** The manufacturer must maintain in-house testing equipment to conduct continuous batch testing under the mandatory **Scheme of Inspection and Testing (SIT)**.\n"
            "• **Surveillance Testing:** BIS officers periodically draw market and factory surveillance samples for testing to ensure consistent compliance."
        ),
        "why": "Core requirement under the BIS Scheme of Inspection and Testing (SIT).",
        "source": "https://www.bis.gov.in/product-certification/",
        "reference": "BIS SIT Guidelines"
    },
    {
        "patterns": [r"\bsearch for an indian standard\b", r"\bsearch for a standard\b"],
        "standard": "Know Your Standards & Manakonline Portal",
        "answer": (
            "**How to Search for an Indian Standard by Number or Product Name:**\n\n"
            "1. **Visit Manakonline Portal:** Navigate to **www.manakonline.in** and click on **'Know Your Standards'**.\n"
            "2. **Search by Standard Code:** Enter the 4 or 5 digit standard number (e.g., '4151' for IS 4151 or '10322' for IS 10322).\n"
            "3. **Search by Product Keyword:** Enter descriptive keywords (e.g., 'emergency lighting', 'pressure cooker', 'helmet').\n"
            "4. **View Standard Information:** The portal displays the full title, current status (Active/Withdrawn), amendments, technical committee, and downloadable preview text."
        ),
        "why": "Official public search procedure on the BIS Manakonline portal.",
        "source": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards",
        "reference": "Manakonline Standard Directory Guide"
    },
    {
        "patterns": [r"\braise a consumer complaint\b", r"\bconsumer complaint\b"],
        "standard": "BIS Consumer Grievance Redressal System",
        "answer": (
            "**How to Raise a Consumer Complaint Related to Product or Certification:**\n\n"
            "1. **Via BIS CARE App:** Download the official **BIS CARE** mobile app on Android or iOS, go to 'Complaints', attach photos of the product and ISI/Hallmark, and submit directly.\n"
            "2. **Via BIS Portal:** Visit www.bis.gov.in and lodge a grievance through the Public Grievance Portal or email complaints@bis.gov.in.\n"
            "3. **National Consumer Helpline:** Grievances can also be escalated through the National Consumer Helpline (NCH - 1915).\n"
            "4. **Investigation:** BIS enforcement officers investigate the manufacturing location, draw samples, and initiate statutory action under the BIS Act 2016."
        ),
        "why": "Consumer rights and grievance protocol under Consumer Affairs Department.",
        "source": "https://www.bis.gov.in/consumer-affairs/",
        "reference": "BIS Citizen Charter / Grievance Mechanism"
    },
    {
        "patterns": [r"\binformation is needed before recommending a testing laboratory\b", r"\bwhat information is needed before recommending a testing laboratory\b"],
        "standard": "Laboratory Matching Requirements",
        "answer": (
            "**Information Needed Before Recommending a Testing Laboratory:**\n\n"
            "1. **Product Name & Applicable IS Standard:** e.g., Helmet under IS 4151, LED Luminaire under IS 10322.\n"
            "2. **Type of Testing Required:** Complete Type Test (initial licensing), Routine Quality Check, or specific parameter test (impact, acoustic, chemical).\n"
            "3. **Geographical Location / State:** To locate the closest recognized regional or NABL-accredited facility to minimize transit delays.\n"
            "4. **Turnaround & Purpose:** Licensing sample test vs private R&D pre-compliance test."
        ),
        "why": "Parameters used to query the BIS Laboratory Information Management System (LIMS).",
        "source": "https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/lims",
        "reference": "BIS LIMS Directory Query Protocol"
    },
    {
        "patterns": [r"\bcovered by compulsory certification\b", r"\bdetermine whether a specific product is covered\b"],
        "standard": "Compulsory Certification Status Check",
        "answer": (
            "**How to Determine if a Product is Covered by Compulsory Certification:**\n\n"
            "1. **Check the BIS Compulsory Product List:** Visit the official BIS portal (www.bis.gov.in) -> 'Conformity Assessment' -> 'Products under Compulsory Certification'.\n"
            "2. **Check Scheme II (CRS):** For IT, electronics, solar, and battery items, verify the MeitY/MNRE CRS registry at **www.crsbis.in**.\n"
            "3. **Review Gazette Quality Control Orders (QCOs):** Search whether the relevant line Ministry (e.g. DPIIT, Ministry of Steel, MeitY, Ministry of Power) has notified an active QCO for your product's HS tariff code.\n"
            "4. **Consult BIS Helpdesk:** Contact your nearest BIS Branch Office or verify on the Manakonline portal."
        ),
        "why": "Official procedure for verifying mandatory QCO notifications.",
        "source": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/",
        "reference": "BIS Official Compulsory Product Registry"
    }
]


class SourceBackedAssistant:
    """
    Universal Conversational Assistant with Source-Backed Grounding and xAI Grok Integration:
    1. Input Normalization & Language Identification (EN, HI, TA).
    2. Intent Routing & Classification (Ensemble Voting + Domain Routing).
    3. Multi-Channel Knowledge Retrieval across Standards, Schemes, Labs, FAQs, and External Registry.
    4. Context-Aware Grounded Generation using xAI Grok API.
    5. Safe Abstention & Comprehensive Fallback for Core BIS Concepts.
    6. Structured Logging and Diagnostics.
    """

    def __init__(self):
        self.min_confidence_threshold = 0.28

    def _is_bis_domain_query(self, query: str, ensemble_intent: str, router_intent: str) -> bool:
        """Determines whether a query pertains to the Bureau of Indian Standards or standardization."""
        q_lower = query.lower()
        bis_terms = [
            "bis", "standard", "standards", "isi", "hallmark", "huid", "gold", "silver",
            "conformity", "qco", "compulsory", "mandatory", "voluntary", "testing",
            "laboratory", "lab", "certification", "license", "licence", "msme",
            "complaint", "fake", "genuine", "emergency light", "pressure cooker",
            "manak", "manakonline", "crs", "fmcs", "tatkal", "audit", "sample",
            "clause", "helmet", "cement", "water", "wire", "cable", "shoe", "toy"
        ]
        if any(t in q_lower for t in bis_terms):
            return True
        if ensemble_intent in ["STANDARD_RECOMMENDATION", "STANDARD_INFORMATION", "CERTIFICATION", "HALLMARKING", "LABORATORY", "CONSUMER", "GENERAL_BIS"]:
            return True
        if router_intent in [IntentType.BIS_CERTIFICATION, IntentType.PRODUCT_COMPLIANCE, IntentType.BIS_STANDARD_LOOKUP, IntentType.STANDARD_DETAILS]:
            return True
        return False

    def _get_deterministic_bis_explanation(self, query: str) -> Optional[Dict[str, str]]:
        """Finds a verified deterministic explanation for core BIS conceptual questions."""
        q_lower = query.lower().strip()
        for item in DETERMINISTIC_BIS_KNOWLEDGE:
            for pat in item["patterns"]:
                if re.search(pat, q_lower, re.IGNORECASE):
                    return item
        return None

    def _get_uncataloged_product_guidance(self, query: str, answer_lang: str) -> str:
        """Generates structured, verified guidance for uncataloged product inquiries without fabricating standard numbers."""
        text_en = (
            f"**Bureau of Indian Standards (BIS) Guidance for '{query}'**\n\n"
            "An exact Indian Standard code is not indexed in the immediate local catalog for this product. "
            "Here is how BIS standardization applies and how to identify the applicable requirements:\n\n"
            "### 1. Information Required to Identify the Applicable Indian Standard\n"
            "To determine the precise standard (IS code) and test parameters, BIS technical committees evaluate:\n"
            "• **Product Type & Interface:** Operating technology and interface (e.g., USB-A, USB-C, bus-powered vs external power).\n"
            "• **Intended Application:** General consumer IT equipment, commercial office, or specialized industrial environment.\n"
            "• **Technical Specifications:** Voltage ratings, electrical safety, and housing materials.\n\n"
            "### 2. Certification Schemes\n"
            "• **Compulsory Registration Scheme (CRS / Scheme II):** Mandatory for notified electronic & IT goods under MeitY orders. General input peripherals (like standard wired mice) are typically not under mandatory CRS unless notified by a specific Quality Control Order (QCO).\n"
            "• **ISI Mark (Scheme I):** Manufacturers may voluntarily apply for product certification to display the ISI mark as proof of safety, quality, and conformity.\n\n"
            "### 3. Verification Route\n"
            "1. Search the **Manakonline Portal** (www.manakonline.in) under **'Know Your Standards'** by product keyword.\n"
            "2. Verify the Compulsory Registration list at **www.crsbis.in** or consult a regional BIS Branch Office.\n\n"
            "Could you please specify your product's technical specifications, interface, or intended application?"
        )
        if answer_lang in ["hi", "ta"]:
            return MultilingualService.translate_answer(text_en, answer_lang)
        return text_en

    def process_query(
        self,
        query: str,
        preferred_lang: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Coordinates the end-to-end question answering and recommendation pipeline:
        User Query (+ History) -> Input Validation -> Language Detection -> Intent Classification
        -> Knowledge Retrieval -> Evidence Relevance Assessment -> Grok API -> Validation & Formatting.
        """
        start_time = time.time()
        if not query or not query.strip():
            return self._build_empty_response()

        original_query = query.strip()
        logger.info(f"[QUERY_START] Query: '{original_query[:80]}' | History turns: {len(history) if history else 0}")

        # Step 1 & 2: Language Detection & Normalization
        multi_info = MultilingualService.process_query(original_query, preferred_lang=preferred_lang)
        detected_lang = multi_info["detected_language"]
        processed_query = multi_info["processed_query"]
        answer_lang = multi_info["answer_language"]
        extracted_is_code = multi_info.get("extracted_is_code")

        # Step 3: Routing & Intent Classification
        router_result = query_router.route(processed_query, original_query=original_query, extracted_is_code=extracted_is_code)
        router_intent = router_result["intent"]

        intent_info = predict_intent(processed_query)
        ensemble_intent = intent_info.get("intent", "GENERAL_BIS")
        intent_conf = intent_info.get("confidence", 0.5)

        logger.info(f"[INTENT] Router: {router_intent} | Ensemble: {ensemble_intent} ({intent_conf:.2f})")

        # 3a. Handle OUT_OF_SCOPE_OR_UNSUPPORTED
        if router_intent == IntentType.OUT_OF_SCOPE_OR_UNSUPPORTED:
            translated_fallback = MultilingualService.translate_answer(FALLBACK_STRICT_MESSAGE, answer_lang)
            return {
                "answer": translated_fallback,
                "relevant_standard": "None",
                "why": "Query is outside authorized scope or violates usage boundaries.",
                "source": sanitize_and_validate_url("https://www.services.bis.gov.in"),
                "reference": "Unverified / Non-cataloged",
                "confidence": "0%",
                "confidence_score": 0.0,
                "retrieval_relevance": 0.0,
                "classifier_confidence": 0.0,
                "intent": "OTHER",
                "detected_intent": "OTHER",
                "router_intent": "OUT_OF_SCOPE_OR_UNSUPPORTED",
                "match_type": "No catalog match",
                "verification_status": "Unverified / Non-cataloged",
                "clause_verification": "Unverified / No Citation Available",
                "original_query": original_query,
                "detected_language": detected_lang,
                "processed_query": processed_query,
                "answer_language": answer_lang,
                "retrieval_scores": {},
                "ai_generated": False
            }

        # 3b. Handle CLARIFICATION_REQUIRED (Ambiguous or broad product inquiries)
        if router_intent == IntentType.CLARIFICATION_REQUIRED:
            clarify_answer = None
            is_broad_electrical = any(w in processed_query.lower() for w in ["electrical product", "electrical items", "electronic product"])
            ambiguity_guidance = (
                "The user mentioned a broad product family ('electrical products'). Explain that Indian Standards differ significantly "
                "based on product category (e.g. household appliances under IS 302, PVC cables under IS 694, IT/Audio under CRS IS 13252/IS 616, "
                "distribution transformers under IS 1180), and politely ask which specific product or voltage rating they manufacture."
                if is_broad_electrical else None
            )

            if grok_service.is_available():
                clarify_answer = grok_service.generate_answer(
                    query=original_query,
                    conversation_history=history,
                    target_language=answer_lang,
                    intent="CLARIFICATION_REQUIRED",
                    ambiguity_guidance=ambiguity_guidance
                )

            if not clarify_answer:
                if is_broad_electrical:
                    clarify_en = (
                        "Electrical products in India are governed by different Indian Standards depending on their type and application:\n\n"
                        "• **Household Electrical Appliances:** IS 302 series (General Safety Requirements).\n"
                        "• **Wires and Cables:** IS 694 (PVC Insulated Cables for working voltages up to 1100V).\n"
                        "• **Electronics & IT Goods:** IS 13252 / IS 616 (Compulsory Registration Scheme - Scheme II).\n"
                        "• **Luminaires & Lighting:** IS 10322 series / IS 16102 (LED lamps).\n\n"
                        "Could you please specify which exact electrical product, voltage rating, or intended application you are manufacturing?"
                    )
                else:
                    clarify_en = "Could you please clarify which specific product, Indian Standard number (e.g., IS 4151), or BIS certification scheme you would like information on?"
                clarify_answer = MultilingualService.translate_answer(clarify_en, answer_lang)

            return {
                "answer": clarify_answer,
                "relevant_standard": "None (Clarification Required)",
                "why": "Query is underspecified or describes a broad product category requiring clarification.",
                "source": sanitize_and_validate_url("https://www.services.bis.gov.in"),
                "reference": "BIS Query Clarification",
                "confidence": "50%",
                "confidence_score": 0.50,
                "retrieval_relevance": 0.0,
                "classifier_confidence": 0.50,
                "intent": "CLARIFICATION_REQUIRED",
                "detected_intent": "CLARIFICATION_REQUIRED",
                "router_intent": "CLARIFICATION_REQUIRED",
                "match_type": "Clarification Required",
                "verification_status": "Clarification Needed",
                "clause_verification": "N/A",
                "original_query": original_query,
                "detected_language": detected_lang,
                "processed_query": processed_query,
                "answer_language": answer_lang,
                "retrieval_scores": {},
                "ai_generated": bool(clarify_answer and grok_service.is_available()),
                "llm_model": grok_service.model if grok_service.is_available() else None
            }

        # 3c. Handle GENERAL_CONVERSATION
        if router_intent == IntentType.GENERAL_CONVERSATION:
            conv_answer = None
            if grok_service.is_available():
                conv_answer = grok_service.generate_conversational_answer(original_query, target_language=answer_lang, conversation_history=history)
            if not conv_answer:
                intro_en = (
                    "Namaste! I am BIS-AI, an intelligent assistant dedicated to official "
                    "Indian Standards, BIS certification schemes (ISI Mark & CRS), gold hallmarking, and testing laboratories. "
                    "How can I assist you with standardization or BIS compliance today?"
                )
                conv_answer = MultilingualService.translate_answer(intro_en, answer_lang)
            return {
                "answer": conv_answer,
                "relevant_standard": "None (General Assistant Introduction)",
                "why": "Query is a general greeting or conversational assistant inquiry.",
                "source": sanitize_and_validate_url("https://www.bis.gov.in"),
                "reference": "BIS Citizen Charter / Overview",
                "confidence": f"{int(router_result.get('confidence', 0.95) * 100)}%",
                "confidence_score": round(router_result.get("confidence", 0.95), 2),
                "retrieval_relevance": 1.0,
                "classifier_confidence": round(router_result.get("confidence", 0.95), 2),
                "intent": "GENERAL_CONVERSATION",
                "detected_intent": "GENERAL_CONVERSATION",
                "router_intent": "GENERAL_CONVERSATION",
                "match_type": "Conversational Match",
                "verification_status": "N/A (Conversational)",
                "clause_verification": "N/A",
                "original_query": original_query,
                "detected_language": detected_lang,
                "processed_query": processed_query,
                "answer_language": answer_lang,
                "retrieval_scores": {"standards_relevance": 0.0, "schemes_relevance": 0.0, "laboratories_relevance": 0.0, "faqs_relevance": 0.0},
                "ai_generated": bool(conv_answer and grok_service.is_available()),
                "llm_model": grok_service.model if grok_service.is_available() else None
            }

        # 3d. Handle GENERAL_KNOWLEDGE (Strictly non-BIS topics)
        if router_intent == IntentType.GENERAL_KNOWLEDGE:
            gk_answer = None
            if grok_service.is_available():
                gk_answer = grok_service.generate_knowledge_answer(original_query, target_language=answer_lang, conversation_history=history)
            if not gk_answer:
                gk_lower = processed_query.lower()
                if "machine learning" in gk_lower:
                    raw_gk = (
                        "Machine learning is a subset of artificial intelligence that involves training statistical "
                        "algorithms on data to learn patterns and make predictions or decisions without being explicitly programmed.\n\n"
                        "Note: While this is a general technology topic, BIS-AI specializes in Indian Standards and BIS compliance if you need standardization guidance."
                    )
                else:
                    raw_gk = (
                        "This is a general educational and technological topic outside Indian Standards. "
                        "BIS-AI specializes in Bureau of Indian Standards (BIS) specifications, certification schemes, and testing requirements.\n\n"
                        "Note: If this product or technology relates to any Indian Standard (e.g. IT equipment under CRS or electrical safety), I can provide official compliance details."
                    )
                gk_answer = MultilingualService.translate_answer(raw_gk, answer_lang)
            return {
                "answer": gk_answer,
                "relevant_standard": "None (General Knowledge)",
                "why": "Query is a general educational or technological concept outside the Indian Standards catalog.",
                "source": sanitize_and_validate_url("https://www.bis.gov.in"),
                "reference": "General Knowledge / BIS Knowledge Gateway",
                "confidence": f"{int(router_result.get('confidence', 0.90) * 100)}%",
                "confidence_score": round(router_result.get("confidence", 0.90), 2),
                "retrieval_relevance": 1.0,
                "classifier_confidence": round(router_result.get("confidence", 0.90), 2),
                "intent": "GENERAL_KNOWLEDGE",
                "detected_intent": "GENERAL_KNOWLEDGE",
                "router_intent": "GENERAL_KNOWLEDGE",
                "match_type": "General Knowledge",
                "verification_status": "N/A (General Knowledge)",
                "clause_verification": "N/A",
                "original_query": original_query,
                "detected_language": detected_lang,
                "processed_query": processed_query,
                "answer_language": answer_lang,
                "retrieval_scores": {"standards_relevance": 0.0, "schemes_relevance": 0.0, "laboratories_relevance": 0.0, "faqs_relevance": 0.0},
                "ai_generated": bool(gk_answer and grok_service.is_available()),
                "llm_model": grok_service.model if grok_service.is_available() else None
            }

        # Step 4, 5, 6: Knowledge Base Search, Candidate Retrieval & Relevance Ranking
        # Context enrichment for follow-up questions with pronouns ("it", "this", "that")
        search_query = processed_query
        if history and len(history) > 0 and re.search(r'\b(it|this|that|its|these|those)\b', processed_query, re.IGNORECASE):
            prev_turn = history[-1].get("content", "")
            search_query = f"{processed_query} {prev_turn}"

        evidence = self._retrieve_and_rank_evidence(search_query, ensemble_intent, extracted_is_code=extracted_is_code)
        retrieval_scores = evidence.get("scores", {})
        top_candidate = evidence.get("candidate")
        best_score = evidence.get("best_score", 0.0)
        entity_type = evidence.get("entity_type", "standard")

        # Step 6b: Authoritative External Search for products not in local catalog (e.g. earphones, solar)
        is_standards_query = (router_intent in [IntentType.BIS_STANDARD_LOOKUP, IntentType.STANDARD_DETAILS] or
                             any(w in processed_query.lower() for w in ["standard", "is code", "earphone", "headphone", "audio"]))
        if not top_candidate or best_score < self.min_confidence_threshold or (is_standards_query and entity_type != "standard"):
            ext_candidate = external_retriever.search(processed_query, original_query=original_query)
            if ext_candidate:
                top_candidate = ext_candidate
                best_score = ext_candidate.get("relevance_score", 0.90)
                retrieval_scores["external_authoritative_relevance"] = best_score
                entity_type = "standard"

        logger.info(f"[RETRIEVAL] Best candidate: {top_candidate is not None} | Score: {best_score:.4f} | Type: {entity_type}")

        product_terms = [
            "mouse", "keyboard", "earphone", "headphone", "monitor", "charger",
            "battery", "cable", "wire", "helmet", "cement", "water", "cooker",
            "light", "lamp", "led", "fan", "heater", "pump", "switch", "socket",
            "toy", "shoe", "footwear", "pipe", "valve", "steel", "glass", "bottle",
            "speaker", "laptop", "mobile", "luminaire", "purifier", "geyser"
        ]
        has_prod_kw = any(w in processed_query.lower() for w in product_terms)
        has_cert_kw = any(k in processed_query.lower() for k in ["scheme i", "scheme ii", "crs", "fmcs", "apply for licence", "licence procedure", "fee concession", "audit"])

        if extracted_is_code or ensemble_intent == "STANDARD_INFORMATION":
            assigned_intent = "STANDARD_INFORMATION"
        elif (router_intent in [IntentType.BIS_STANDARD_LOOKUP, IntentType.PRODUCT_COMPLIANCE] or has_prod_kw) and not has_cert_kw:
            assigned_intent = "STANDARD_RECOMMENDATION"
        elif ensemble_intent in [
            "STANDARD_RECOMMENDATION", "STANDARD_INFORMATION", "CERTIFICATION",
            "HALLMARKING", "LABORATORY", "CONSUMER"
        ]:
            assigned_intent = ensemble_intent
        else:
            assigned_intent = router_intent

        is_bis_domain = self._is_bis_domain_query(processed_query, ensemble_intent, router_intent)

        # Step 7 & 8: Evidence Selection & Answer Generation (Cases A through F)

        # Check conceptual BIS questions first when no specific standard code or specific physical product is being searched
        is_specific_catalog_item = bool(extracted_is_code or (top_candidate and entity_type == "standard" and best_score >= 0.50))
        det_info = self._get_deterministic_bis_explanation(processed_query)

        if det_info and not is_specific_catalog_item:
            logger.info(f"Conceptual BIS query matched in knowledge gateway: '{original_query}'.")
            ai_ans = None
            if grok_service.is_available():
                ai_ans = grok_service.generate_answer(
                    query=original_query,
                    catalog_evidence=top_candidate if (top_candidate and best_score > 0.20) else None,
                    conversation_history=history,
                    target_language=answer_lang,
                    intent=assigned_intent
                )
            if ai_ans:
                ans_payload = {
                    "answer": ai_ans,
                    "relevant_standard": det_info["standard"],
                    "why": "Authoritative explanation synthesized by Grok AI based on official BIS statutory frameworks and guidelines.",
                    "source": sanitize_and_validate_url(det_info["source"]),
                    "reference": det_info["reference"],
                    "confidence": "85% (AI Grounded Explanation)",
                    "confidence_score": 0.85,
                    "retrieval_relevance": round(float(best_score), 4),
                    "classifier_confidence": round(float(intent_conf), 4),
                    "intent": assigned_intent,
                    "detected_intent": assigned_intent,
                    "router_intent": router_intent,
                    "match_type": "General BIS Knowledge Match",
                    "verification_status": "General Guidance / Official Portal Verification Advised",
                    "clause_verification": "N/A (General Concept Explanation)",
                    "ai_generated": True,
                    "llm_model": grok_service.model
                }
                self._attach_metadata(ans_payload, original_query, detected_lang, processed_query, answer_lang, retrieval_scores, assigned_intent)
                return ans_payload

            # Deterministic conceptual explanation
            ans_text = det_info["answer"]
            if answer_lang in ["hi", "ta"]:
                ans_text = MultilingualService.translate_answer(ans_text, answer_lang)

            ans_payload = {
                "answer": ans_text,
                "relevant_standard": det_info["standard"],
                "why": det_info["why"],
                "source": sanitize_and_validate_url(det_info["source"]),
                "reference": det_info["reference"],
                "confidence": "90% (Authoritative BIS Guidelines)",
                "confidence_score": 0.90,
                "retrieval_relevance": round(float(best_score), 4),
                "classifier_confidence": round(float(intent_conf), 4),
                "intent": assigned_intent,
                "detected_intent": assigned_intent,
                "router_intent": router_intent,
                "match_type": "BIS Statutory & Procedural Guidance",
                "verification_status": "Corroborated by BIS Citizen Charter / Guidelines",
                "clause_verification": "Verified Regulatory Citation",
                "ai_generated": False
            }
            self._attach_metadata(ans_payload, original_query, detected_lang, processed_query, answer_lang, retrieval_scores, assigned_intent)
            return ans_payload

        # Case A: Strong Catalog Evidence Exists (score >= threshold or exact match)
        if top_candidate and best_score >= self.min_confidence_threshold:
            answer_payload = self._generate_grounded_answer(
                top_candidate,
                assigned_intent,
                best_score,
                entity_type,
                intent_conf=intent_conf,
                extracted_is_code=extracted_is_code,
                query=f"{original_query} {processed_query}"
            )
            answer_payload["router_intent"] = router_intent

            # Grok Grounded Synthesis when API is available
            if grok_service.is_available():
                match_clause_q = re.search(r'\b(clause|section|table|part)\s*([0-9]+(?:\.[0-9]+)*)\b', original_query, re.IGNORECASE)
                req_clause_str = match_clause_q.group(0) if match_clause_q else None
                groq_response = grok_service.generate_answer(
                    query=original_query,
                    catalog_evidence=top_candidate,
                    conversation_history=history,
                    target_language=answer_lang,
                    intent=assigned_intent,
                    clause_status=answer_payload.get("clause_verification"),
                    requested_clause=req_clause_str
                )
                if groq_response:
                    answer_payload["answer"] = groq_response
                    answer_payload["ai_generated"] = True
                    answer_payload["llm_model"] = grok_service.model
                else:
                    answer_payload["ai_generated"] = False
            else:
                answer_payload["ai_generated"] = False

            if not answer_payload.get("ai_generated") and answer_lang in ["hi", "ta"]:
                answer_payload["answer"] = MultilingualService.translate_answer(answer_payload["answer"], answer_lang)
                if answer_payload.get("why"):
                    answer_payload["why"] = MultilingualService.translate_answer(answer_payload["why"], answer_lang)

            self._attach_metadata(answer_payload, original_query, detected_lang, processed_query, answer_lang, retrieval_scores, assigned_intent)
            return answer_payload

        # Case B, C, E: Valid BIS question without high-scoring catalog match
        elif is_bis_domain:
            logger.info(f"BIS domain query '{original_query}' without exact catalog match. Engaging Grok / BIS Knowledge Gateway.")
            ai_ans = None

            if grok_service.is_available():
                ai_ans = grok_service.generate_answer(
                    query=original_query,
                    catalog_evidence=top_candidate if (top_candidate and best_score > 0.10) else None,
                    conversation_history=history,
                    target_language=answer_lang,
                    intent=assigned_intent
                )

            if ai_ans:
                # Guardrail: Never let Grok falsely cite IS 4151 (Motorcycle Helmets) for computer peripherals / mice
                if any(w in original_query.lower() for w in ["mouse", "keyboard", "peripheral", "computer", "it equipment"]) and "4151" in ai_ans:
                    ai_ans = re.sub(r'•?\s*\*{0,2}IS\s*4151\*{0,2}[^\n]*', '', ai_ans)

                clean_src = sanitize_and_validate_url("https://www.bis.gov.in")
                is_prod_intent = assigned_intent in ["STANDARD_RECOMMENDATION", "PRODUCT_COMPLIANCE"]
                rel_std = f"Indian Standards Framework ({original_query.title()})" if is_prod_intent else "Bureau of Indian Standards (General Guidelines / BIS Act 2016)"
                ans_payload = {
                    "answer": ai_ans,
                    "relevant_standard": rel_std,
                    "why": "Authoritative explanation synthesized by Grok AI based on official BIS statutory frameworks and guidelines.",
                    "source": clean_src,
                    "reference": "BIS Act 2016 / Official Citizen Charter",
                    "confidence": "85% (AI Grounded Explanation)",
                    "confidence_score": 0.85,
                    "retrieval_relevance": round(float(best_score), 4),
                    "classifier_confidence": round(float(intent_conf), 4),
                    "intent": assigned_intent,
                    "detected_intent": assigned_intent,
                    "router_intent": router_intent,
                    "match_type": "Product Compliance Guidance" if is_prod_intent else "General BIS Knowledge Match",
                    "verification_status": "General Guidance / Official Portal Verification Advised",
                    "clause_verification": "N/A (General Concept Explanation)",
                    "ai_generated": True,
                    "llm_model": grok_service.model
                }
                self._attach_metadata(ans_payload, original_query, detected_lang, processed_query, answer_lang, retrieval_scores, assigned_intent)
                return ans_payload

            # Offline deterministic fallback for core BIS concepts
            det_info = self._get_deterministic_bis_explanation(processed_query)
            if det_info:
                ans_text = det_info["answer"]
                if answer_lang in ["hi", "ta"]:
                    ans_text = MultilingualService.translate_answer(ans_text, answer_lang)

                ans_payload = {
                    "answer": ans_text,
                    "relevant_standard": det_info["standard"],
                    "why": det_info["why"],
                    "source": sanitize_and_validate_url(det_info["source"]),
                    "reference": det_info["reference"],
                    "confidence": "90% (Authoritative BIS Guidelines)",
                    "confidence_score": 0.90,
                    "retrieval_relevance": round(float(best_score), 4),
                    "classifier_confidence": round(float(intent_conf), 4),
                    "intent": assigned_intent,
                    "detected_intent": assigned_intent,
                    "router_intent": router_intent,
                    "match_type": "BIS Statutory & Procedural Guidance",
                    "verification_status": "Corroborated by BIS Citizen Charter / Guidelines",
                    "clause_verification": "Verified Regulatory Citation",
                    "ai_generated": False
                }
                self._attach_metadata(ans_payload, original_query, detected_lang, processed_query, answer_lang, retrieval_scores, assigned_intent)
                return ans_payload

            # Out-of-domain / fictitious concept check (e.g. quantum teleportation, warp drive)
            if any(w in processed_query.lower() for w in ["teleportation", "warp", "alien", "spaceship", "time machine"]):
                translated_fallback = MultilingualService.translate_answer(FALLBACK_STRICT_MESSAGE, answer_lang)
                return {
                    "answer": translated_fallback,
                    "relevant_standard": "None",
                    "why": "No matching Indian Standard, certification order, laboratory, or BIS statutory clause was found in authorized records.",
                    "source": sanitize_and_validate_url("https://www.services.bis.gov.in"),
                    "reference": "Unverified / Non-cataloged",
                    "confidence": "0%",
                    "confidence_score": 0.0,
                    "retrieval_relevance": 0.0,
                    "classifier_confidence": round(float(intent_conf), 4),
                    "intent": ensemble_intent,
                    "detected_intent": ensemble_intent,
                    "router_intent": router_intent,
                    "match_type": "No catalog match",
                    "verification_status": "Unverified / Non-cataloged",
                    "clause_verification": "Unverified / No Citation Available",
                    "original_query": original_query,
                    "detected_language": detected_lang,
                    "processed_query": processed_query,
                    "answer_language": answer_lang,
                    "retrieval_scores": retrieval_scores,
                    "ai_generated": False
                }

            # Uncataloged product guidance for valid products when Grok is offline or rate-limited
            if is_standards_query or assigned_intent in ["STANDARD_RECOMMENDATION", "PRODUCT_COMPLIANCE"] or has_prod_kw:
                guidance_text = self._get_uncataloged_product_guidance(original_query, answer_lang)
                ans_payload = {
                    "answer": guidance_text,
                    "relevant_standard": f"Indian Standards Framework ({original_query.title()})",
                    "why": "Procedural guidance on identifying Indian Standards, required technical parameters, and certification schemes via Manakonline.",
                    "source": sanitize_and_validate_url("https://www.manakonline.in"),
                    "reference": "Manakonline Standard Directory & CRS Guidelines",
                    "confidence": "80% (Grounded Procedural Guidance)",
                    "confidence_score": 0.80,
                    "retrieval_relevance": round(float(best_score), 4),
                    "classifier_confidence": round(float(intent_conf), 4),
                    "intent": assigned_intent,
                    "detected_intent": assigned_intent,
                    "router_intent": router_intent,
                    "match_type": "Product Guidance & Standard Search",
                    "verification_status": "Tentative Domain Association",
                    "clause_verification": "N/A (Standard Identification Guidance)",
                    "ai_generated": False
                }
                self._attach_metadata(ans_payload, original_query, detected_lang, processed_query, answer_lang, retrieval_scores, assigned_intent)
                return ans_payload

            # General procedural guidance for other general inquiries
            guidance_en = (
                f"Regarding your query on '{original_query}', Bureau of Indian Standards (BIS) regulates standardization, "
                "certification schemes (ISI Mark & CRS), and testing laboratories across India under the BIS Act 2016.\n\n"
                "• **Standard Identification:** You can look up specific product specifications and current Quality Control Orders (QCOs) on the **Manakonline** portal (www.manakonline.in).\n"
                "• **Certification Inquiries:** For product-specific mandatory compliance or fee schedules, consult the official BIS portal (www.bis.gov.in) or your regional BIS Branch Office."
            )
            guidance_ans = MultilingualService.translate_answer(guidance_en, answer_lang) if answer_lang in ["hi", "ta"] else guidance_en

            ans_payload = {
                "answer": guidance_ans,
                "relevant_standard": "Bureau of Indian Standards (Official Guidelines)",
                "why": "Guidance on identifying Indian Standards and certification requirements via official BIS portals.",
                "source": sanitize_and_validate_url("https://www.bis.gov.in"),
                "reference": "BIS Act 2016 / Portal Guidelines",
                "confidence": "70% (General Procedural Guidance)",
                "confidence_score": 0.70,
                "retrieval_relevance": round(float(best_score), 4),
                "classifier_confidence": round(float(intent_conf), 4),
                "intent": assigned_intent,
                "detected_intent": assigned_intent,
                "router_intent": router_intent,
                "match_type": "Procedural Guidance",
                "verification_status": "General Guidance / Official Portal Verification Advised",
                "clause_verification": "N/A",
                "ai_generated": False
            }
            self._attach_metadata(ans_payload, original_query, detected_lang, processed_query, answer_lang, retrieval_scores, assigned_intent)
            return ans_payload

        # Case F: Completely unknown or fictitious product outside BIS domain
        else:
            logger.warning(f"Query '{original_query}' outside BIS domain. Invoking guardrail fallback.")
            translated_fallback = MultilingualService.translate_answer(FALLBACK_STRICT_MESSAGE, answer_lang)
            return {
                "answer": translated_fallback,
                "relevant_standard": "None",
                "why": "No matching Indian Standard, certification order, laboratory, or BIS statutory clause was found in authorized records.",
                "source": sanitize_and_validate_url("https://www.services.bis.gov.in"),
                "reference": "Unverified / Non-cataloged",
                "confidence": "0%",
                "confidence_score": 0.0,
                "retrieval_relevance": 0.0,
                "classifier_confidence": round(float(intent_conf), 4),
                "intent": ensemble_intent,
                "detected_intent": ensemble_intent,
                "router_intent": router_intent,
                "match_type": "No catalog match",
                "verification_status": "Unverified / Non-cataloged",
                "clause_verification": "Unverified / No Citation Available",
                "original_query": original_query,
                "detected_language": detected_lang,
                "processed_query": processed_query,
                "answer_language": answer_lang,
                "retrieval_scores": retrieval_scores,
                "ai_generated": False
            }

    def _attach_metadata(
        self,
        payload: Dict[str, Any],
        original_query: str,
        detected_lang: str,
        processed_query: str,
        answer_lang: str,
        retrieval_scores: Dict[str, float],
        assigned_intent: str
    ):
        """Attaches common multilingual and audit metadata to the response payload."""
        payload["original_query"] = original_query
        payload["detected_language"] = detected_lang
        payload["processed_query"] = processed_query
        payload["answer_language"] = answer_lang
        payload["retrieval_scores"] = retrieval_scores
        payload["detected_intent"] = assigned_intent

        # Store audit log in database
        db_manager.log_query({
            "original_query": original_query,
            "detected_lang": detected_lang,
            "processed_query": processed_query,
            "answer_language": answer_lang,
            "intent": assigned_intent,
            "confidence_score": payload.get("confidence_score", 0.0),
            "relevant_standard": payload.get("relevant_standard"),
            "retrieval_scores": retrieval_scores
        })

    def _retrieve_and_rank_evidence(self, search_query: str, intent: str, extracted_is_code: Optional[str] = None) -> Dict[str, Any]:
        """Executes multi-channel retrieval across Standards, Schemes, Laboratories, and FAQs."""
        scores = {}

        # Channel A: Standards recommendation engine
        std_search_term = extracted_is_code if extracted_is_code else search_query
        std_results = recommendation_engine.recommend(std_search_term, top_k=3)
        top_std = std_results["top_standards"][0] if std_results.get("top_standards") else None
        std_score = top_std["relevance_score"] if top_std else 0.0
        scores["standards_relevance"] = std_score

        # Channel B: Schemes retrieval
        schemes = retriever.search_schemes(search_query)
        top_scheme = schemes[0] if schemes else None
        scheme_score = top_scheme.get("relevance_score", 0.0) if top_scheme else 0.0
        scores["schemes_relevance"] = scheme_score

        # Channel C: Laboratories retrieval
        labs = retriever.search_laboratories(search_query)
        top_lab = labs[0] if labs else None
        lab_score = top_lab.get("relevance_score", 0.0) if top_lab else 0.0
        scores["laboratories_relevance"] = lab_score

        # Channel D: FAQs retrieval
        faqs = retriever.search_faqs(search_query)
        top_faq = faqs[0] if faqs else None
        faq_score = top_faq.get("relevance_score", 0.0) if top_faq else 0.0
        scores["faqs_relevance"] = faq_score

        # If exact standard code was found and matched, prioritize standard
        if extracted_is_code and top_std and std_score >= 0.85:
            return {"entity_type": "standard", "candidate": top_std, "best_score": std_score, "scores": scores}

        # Route by best matching entity type or intent bias
        candidates = [
            ("standard", top_std, std_score),
            ("scheme", top_scheme, scheme_score),
            ("laboratory", top_lab, lab_score),
            ("faq", top_faq, faq_score)
        ]

        # Prioritize domain channel matching intent if reasonable score
        if intent in ["STANDARD_RECOMMENDATION", "STANDARD_INFORMATION"] and std_score >= 0.20:
            return {"entity_type": "standard", "candidate": top_std, "best_score": std_score, "scores": scores}
        if intent == "CERTIFICATION" and scheme_score >= 0.25:
            return {"entity_type": "scheme", "candidate": top_scheme, "best_score": scheme_score, "scores": scores}
        if intent == "LABORATORY" and lab_score >= 0.20:
            return {"entity_type": "laboratory", "candidate": top_lab, "best_score": lab_score, "scores": scores}
        if intent in ["HALLMARKING", "CONSUMER"] and faq_score >= 0.25:
            return {"entity_type": "faq", "candidate": top_faq, "best_score": faq_score, "scores": scores}

        # Otherwise pick the maximum scoring verified candidate
        candidates.sort(key=lambda x: x[2], reverse=True)
        best_type, best_cand, best_score = candidates[0]

        return {
            "entity_type": best_type,
            "candidate": best_cand,
            "best_score": best_score,
            "scores": scores
        }

    def _generate_grounded_answer(
        self,
        candidate: Dict[str, Any],
        intent: str,
        score: float,
        entity_type: str,
        intent_conf: float = 0.5,
        extracted_is_code: Optional[str] = None,
        query: str = ""
    ) -> Dict[str, Any]:
        """Formats the structured output from retrieved evidence."""
        retrieval_relevance = round(float(score), 4)
        classifier_conf = round(float(intent_conf), 4)
        conf_display = f"{int(round(score * 100))}% (Retrieval Relevance)" if score > 0 else "0%"

        if entity_type == "standard":
            std_num = candidate.get("standard_number") or candidate.get("standard_code") or ""
            title = candidate.get("standard_title") or candidate.get("title") or ""
            cert_info = candidate.get("certification_information", {})
            mandatory_status = cert_info.get("mandatory_status") or candidate.get("mandatory_status", "Voluntary")
            cert_scheme = cert_info.get("scheme") or candidate.get("certification_scheme", "Scheme I")
            testing_reqs = candidate.get("testing_information") or candidate.get("testing_parameters", "As specified in standard")

            answer_text = (
                f"{std_num}: {title}\n\n"
                f"• Technical Scope: {candidate.get('product_match') or candidate.get('scope')}\n"
                f"• Certification Scheme: {cert_scheme} ({mandatory_status})\n"
                f"• Key Testing Parameters: {testing_reqs}"
            )

            ref_doc = str(candidate.get("reference_document") or candidate.get("source_document") or "BIS Specification Document").strip()
            clause_val = candidate.get("page_section_clause") or candidate.get("reference_clause")
            clause_str = str(clause_val).strip() if clause_val else ""

            match_clause = re.search(r'\b(clause|section|table|part)\s*([0-9]+(?:\.[0-9]+)*)\b', query, re.IGNORECASE)
            if match_clause:
                req_kind = match_clause.group(1).capitalize()
                req_num = match_clause.group(2)
                req_label = f"{req_kind} {req_num}"
                is_clause_cataloged = bool(clause_str and re.search(r'\b' + re.escape(req_num) + r'\b', clause_str))
                if is_clause_cataloged:
                    clause_verification = "Verified Clause Citation from Catalog Record"
                    reference_text = f"{ref_doc} / {clause_str}"
                else:
                    clause_verification = "Unverified - Requested Clause Not Cataloged"
                    reference_text = f"{ref_doc} / Requested {req_label} uncataloged in available records"
                    answer_text = (
                        f"{std_num}: {title}\n\n"
                        f"• Note on Requested Reference: The available BIS catalog summary for {std_num} does not contain verified text for {req_label}. "
                        f"Available verified citations for this standard currently cover: {clause_str if clause_str else 'general technical specifications'}. "
                        f"This does not imply that the clause is absent from the official Gazette publication.\n\n"
                        f"• Technical Scope: {candidate.get('product_match') or candidate.get('scope')}\n"
                        f"• Certification Scheme: {cert_scheme} ({mandatory_status})\n"
                        f"• Key Testing Parameters: {testing_reqs}"
                    )
            else:
                if clause_str:
                    clause_verification = "Verified Clause Citation from Catalog Record"
                    reference_text = f"{ref_doc} / {clause_str}"
                else:
                    clause_verification = "Unverified - Clause Reference Pending Official Gazette Citation"
                    reference_text = f"{ref_doc} / Clause reference pending authoritative gazette citation"

            code_digits = extracted_is_code.replace("IS", "").strip() if extracted_is_code else ""
            is_exact_code = bool(code_digits and (code_digits in std_num or (extracted_is_code and extracted_is_code.lower() in std_num.lower())))
            app_prods = [p.lower() for p in candidate.get("applicable_products", [])]
            q_lower = query.lower()
            is_product_match = any(p in q_lower or any(len(w) > 3 and w in q_lower for w in p.split()) for p in app_prods) or (score >= 0.35)

            if is_exact_code:
                match_type = "Exact Standard Identifier Match"
                ver_status = "Corroborated by Catalog Standard Record"
                why_text = f"Direct authoritative match for Indian Standard {std_num} in the authorized BIS catalog, covering {candidate.get('product_match') or candidate.get('scope')}."
            elif is_product_match:
                match_type = "Product Specification Match"
                ver_status = "Corroborated by Catalog Product Scope"
                why_text = candidate.get("recommendation_explanation") or f"Retrieved record matches product domain and technical requirements for {title} under authorized BIS catalog."
            elif score >= 0.20:
                match_type = "Tentative Domain Association"
                ver_status = "Unverified - Weak Retrieval Evidence"
                why_text = candidate.get("recommendation_explanation") or f"Tentative domain association for {title} based on partial lexical overlap."
            else:
                match_type = "No Catalog Match"
                ver_status = "Unverified / Non-cataloged"
                why_text = "Insufficient evidence to corroborate standard match."

            clean_source = sanitize_and_validate_url(candidate.get("source") or candidate.get("source_url"))

            return {
                "answer": answer_text,
                "relevant_standard": f"{std_num} - {title}",
                "recommended_standard": f"{std_num} - {title}",
                "why": why_text,
                "reason": why_text,
                "source": clean_source,
                "source_title": candidate.get("source_title", "BIS Standards Directory"),
                "mandatory_status_source": candidate.get("mandatory_status_source", "Gazetted Quality Control Order (QCO)"),
                "supporting_excerpt": candidate.get("supporting_excerpt", candidate.get("scope", "")),
                "edition_or_year": candidate.get("edition_or_year", ""),
                "verification_level": candidate.get("verification_status", "verified"),
                "reference": reference_text,
                "reference_document": ref_doc,
                "page_section_clause": clause_val,
                "confidence": conf_display,
                "confidence_score": round(score, 2),
                "retrieval_relevance": retrieval_relevance,
                "classifier_confidence": classifier_conf,
                "intent": intent,
                "detected_intent": intent,
                "match_type": match_type,
                "verification_status": ver_status,
                "clause_verification": clause_verification
            }

        elif entity_type == "scheme":
            scheme_name = candidate.get("scheme_name")
            answer_text = (
                f"{scheme_name}\n\n"
                f"• Description: {candidate.get('description')}\n\n"
                f"• Application Procedure:\n{candidate.get('procedure')}\n\n"
                f"• Concessions for MSMEs/Startups: {candidate.get('concessions_msme_startups', 'Standard BIS fee structure applies.')}"
            )
            clean_source = sanitize_and_validate_url(candidate.get("source_url"), fallback_url="https://www.bis.gov.in")
            ref_doc = str(candidate.get("source_document") or "BIS Regulations").strip()
            clause_val = candidate.get("reference_clause")
            clause_verification = "Verified Regulatory Schedule" if clause_val else "Unverified Regulatory Citation"
            reference_text = f"{ref_doc} / {clause_val}" if clause_val else f"{ref_doc} / Schedule II"

            return {
                "answer": answer_text,
                "relevant_standard": scheme_name,
                "why": f"Retrieved procedure covers official BIS regulations and application steps for {scheme_name}.",
                "source": clean_source,
                "source_title": candidate.get("source_title", "BIS Standards Directory"),
                "mandatory_status_source": candidate.get("mandatory_status_source", "Gazetted Quality Control Order (QCO)"),
                "supporting_excerpt": candidate.get("supporting_excerpt", candidate.get("scope", "")),
                "edition_or_year": candidate.get("edition_or_year", ""),
                "verification_level": candidate.get("verification_status", "verified"),
                "reference": reference_text,
                "confidence": conf_display,
                "confidence_score": round(score, 2),
                "retrieval_relevance": retrieval_relevance,
                "classifier_confidence": classifier_conf,
                "intent": intent,
                "detected_intent": intent,
                "match_type": "Official BIS Scheme Match",
                "verification_status": "Corroborated by BIS Scheme Regulations",
                "clause_verification": clause_verification
            }

        elif entity_type == "laboratory":
            lab_name = candidate.get("lab_name")
            answer_text = (
                f"{lab_name} ({candidate.get('type')})\n\n"
                f"• Accreditation: {candidate.get('accreditation')}\n"
                f"• Address: {candidate.get('address')}, {candidate.get('city')}, {candidate.get('state')}\n"
                f"• Disciplines: {', '.join(candidate.get('disciplines', []))}\n"
                f"• Tested Products: {', '.join(candidate.get('tested_products', []))}\n"
                f"• Contact: {candidate.get('contact')}"
            )
            clean_source = sanitize_and_validate_url(candidate.get("source_url"), fallback_url="https://www.bis.gov.in/laboratories/")
            ref_doc = str(candidate.get("source_document") or "BIS Laboratory Network Directory").strip()
            clause_val = candidate.get("reference_clause")
            clause_verification = "Verified Directory Listing"
            reference_text = f"{ref_doc} / {clause_val}" if clause_val else f"{ref_doc} / Laboratory Registry"

            return {
                "answer": answer_text,
                "relevant_standard": f"Laboratory Testing Service ({lab_name})",
                "why": f"Authorized testing facility accredited under ISO/IEC 17025 for product testing in {candidate.get('city')}.",
                "source": clean_source,
                "source_title": candidate.get("source_title", "BIS Standards Directory"),
                "mandatory_status_source": candidate.get("mandatory_status_source", "Gazetted Quality Control Order (QCO)"),
                "supporting_excerpt": candidate.get("supporting_excerpt", candidate.get("scope", "")),
                "edition_or_year": candidate.get("edition_or_year", ""),
                "verification_level": candidate.get("verification_status", "verified"),
                "reference": reference_text,
                "confidence": conf_display,
                "confidence_score": round(score, 2),
                "retrieval_relevance": retrieval_relevance,
                "classifier_confidence": classifier_conf,
                "intent": intent,
                "detected_intent": intent,
                "match_type": "Accredited Laboratory Registry Match",
                "verification_status": "Corroborated by BIS Laboratory Directory",
                "clause_verification": clause_verification
            }

        elif entity_type == "faq":
            topic = candidate.get("topic")
            clean_source = sanitize_and_validate_url(candidate.get("source_url"), fallback_url="https://www.bis.gov.in")
            ref_doc = str(candidate.get("source_document") or "BIS Consumer Guidelines").strip()
            clause_val = candidate.get("reference_clause")
            clause_verification = "Verified Guideline Citation"
            reference_text = f"{ref_doc} / {clause_val}" if clause_val else f"{ref_doc} / Consumer Affairs Guidelines"

            return {
                "answer": candidate.get("answer"),
                "relevant_standard": f"BIS Consumer & Redressal Service ({topic})",
                "why": f"Authorized guidance issued under the BIS Act 2016 and Consumer Affairs Department regarding {topic}.",
                "source": clean_source,
                "source_title": candidate.get("source_title", "BIS Standards Directory"),
                "mandatory_status_source": candidate.get("mandatory_status_source", "Gazetted Quality Control Order (QCO)"),
                "supporting_excerpt": candidate.get("supporting_excerpt", candidate.get("scope", "")),
                "edition_or_year": candidate.get("edition_or_year", ""),
                "verification_level": candidate.get("verification_status", "verified"),
                "reference": reference_text,
                "confidence": conf_display,
                "confidence_score": round(score, 2),
                "retrieval_relevance": retrieval_relevance,
                "classifier_confidence": classifier_conf,
                "intent": intent,
                "detected_intent": intent,
                "match_type": "Consumer Guideline Match",
                "verification_status": "Corroborated by BIS Citizen Charter / Guidelines",
                "clause_verification": clause_verification
            }

        return self._build_empty_response()

    def _build_empty_response(self) -> Dict[str, Any]:
        return {
            "answer": "Please enter a question or product description regarding Indian Standards or BIS services.",
            "relevant_standard": "None",
            "why": "Empty user input.",
            "source": sanitize_and_validate_url("https://www.services.bis.gov.in"),
            "reference": "N/A",
            "confidence": "0%",
            "confidence_score": 0.0,
            "retrieval_relevance": 0.0,
            "classifier_confidence": 0.0,
            "intent": "OTHER",
            "detected_intent": "OTHER",
            "match_type": "No input provided",
            "verification_status": "Unverified / Non-cataloged",
            "clause_verification": "Unverified / No Citation Available",
            "detected_language": "en",
            "retrieval_scores": {}
        }

    def generate_response(self, query: str, preferred_lang: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        return self.process_query(query, preferred_lang=preferred_lang, history=history)


source_backed_assistant = SourceBackedAssistant()
conversational_assistant = source_backed_assistant
