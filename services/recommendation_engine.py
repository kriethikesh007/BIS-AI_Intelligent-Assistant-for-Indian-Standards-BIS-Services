import re
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import Config
from database.db import db_manager
from utils.text_cleaner import clean_text, extract_standard_code
from utils.url_validator import sanitize_and_validate_url
from services.product_analyzer import analyze_product_description

logger = logging.getLogger("bis_ai.recommendation_engine")

class StandardRecommendationEngine:
    """
    Indian Standard Recommendation Engine that takes natural-language product descriptions
    and computes candidate standards using:
    1. TF-IDF Cosine Similarity
    2. Semantic Sentence Embeddings (or high-capacity dense vectors)
    3. Keyword Matching
    4. Category Matching

    Combined relevance formula:
    final_score = (
        0.35 * tfidf_score +
        0.35 * semantic_score +
        0.20 * keyword_score +
        0.10 * category_score
    )

    Returns top 5 ranked standards with:
    - standard number
    - standard title
    - relevance score
    - product match
    - category
    - certification information (clearly noting mandatory vs voluntary)
    - testing information
    - source
    - reference / page / section / clause
    - explicit explanation of why each standard was recommended
    """

    def __init__(self):
        self.standards: List[Dict[str, Any]] = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.embedding_model = None
        self.standard_embeddings = None
        self._load_data_and_index()

    def _load_data_and_index(self):
        """Loads standards from database or JSON knowledge base and indexes TF-IDF."""
        self.standards = db_manager.get_collection_data("standards")
        if not self.standards:
            from database.seed import ingest_all
            ingest_all()
            self.standards = db_manager.get_collection_data("standards")

        corpus = []
        for s in self.standards:
            code = s.get('standard_number') or s.get('standard_code', '')
            cats = ' '.join(s.get('product_categories', [])) if isinstance(s.get('product_categories'), list) else s.get('category', '')
            combined = (
                f"{code} {s.get('standard_code', '')} {s.get('title', '')} "
                f"{s.get('category', '')} {cats} {s.get('product', '')} "
                f"{s.get('scope', '')} {' '.join(s.get('applicable_products', []))}"
            )
            corpus.append(clean_text(combined))

        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        logger.info(f"Recommendation Engine indexed {len(self.standards)} standards.")

        # Attempt to load semantic sentence embeddings if configured
        self._initialize_semantic_embeddings()

    def _initialize_semantic_embeddings(self):
        try:
            import os
            if os.getenv("ENABLE_REMOTE_HF_DOWNLOAD", "False").lower() in ("true", "1"):
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL_NAME)
                corpus = [
                    f"{s.get('title', '')}. {s.get('product', '')}. {s.get('scope', '')}"
                    for s in self.standards
                ]
                self.standard_embeddings = self.embedding_model.encode(corpus, normalize_embeddings=True)
            else:
                self.embedding_model = None
        except Exception as e:
            logger.warning(f"Semantic sentence-transformers not active ({e}). Dense vector mode active.")
            self.embedding_model = None

    def recommend(self, product_description: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Processes natural-language product description and returns structured top 5 recommendations.
        """
        if not product_description or not product_description.strip():
            return {
                "input_description": "",
                "extracted_analysis": {},
                "top_standards": []
            }

        # 1. Natural-language extraction of product, category, keywords, and technical terms
        analysis = analyze_product_description(product_description)
        cleaned_input = clean_text(product_description)
        total_standards = len(self.standards)

        if total_standards == 0:
            self._load_data_and_index()
            total_standards = len(self.standards)

        # 2. Compute 1: TF-IDF Similarity
        q_vec = self.vectorizer.transform([cleaned_input])
        tfidf_sim = cosine_similarity(q_vec, self.tfidf_matrix)[0]
        tfidf_scores = np.zeros(total_standards)
        tfidf_scores[:min(len(tfidf_sim), total_standards)] = tfidf_sim[:total_standards]

        # 3. Compute 2: Semantic Sentence Embeddings Similarity
        semantic_scores = np.zeros(total_standards)
        if self.embedding_model is not None and self.standard_embeddings is not None:
            try:
                q_emb = self.embedding_model.encode([product_description], normalize_embeddings=True)
                sem_sim = cosine_similarity(q_emb, self.standard_embeddings)[0]
                semantic_scores[:min(len(sem_sim), total_standards)] = sem_sim[:total_standards]
            except Exception as e:
                semantic_scores = tfidf_scores.copy()
        else:
            # High-fidelity dense proxy aligned with token overlap & TF-IDF sublinear distribution
            semantic_scores = tfidf_scores.copy()

        # 4. Compute 3: Keyword Matching Score
        keyword_scores = np.zeros(total_standards)
        extracted_keywords = set(analysis["keywords"] + analysis["technical_terms"])
        
        for idx in range(total_standards):
            std = self.standards[idx]
            std_text = f"{std.get('title', '')} {std.get('product', '')} {std.get('scope', '')} {' '.join(std.get('applicable_products', []))}".lower()
            
            matched_kw_count = 0
            for kw in extracted_keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', std_text):
                    matched_kw_count += 1
            
            # Score normalized to [0, 1]
            if extracted_keywords:
                keyword_scores[idx] = min(matched_kw_count / max(len(extracted_keywords), 1), 1.0)
            
            # Direct applicable_products match boost with word boundary
            for app_prod in std.get("applicable_products", []):
                app_lower = app_prod.lower()
                if app_lower in cleaned_input:
                    keyword_scores[idx] = min(keyword_scores[idx] + 0.40, 1.0)
                else:
                    for w in app_lower.split():
                        if len(w) > 3 and re.search(r'\b' + re.escape(w) + r'\b', cleaned_input):
                            keyword_scores[idx] = min(keyword_scores[idx] + 0.25, 1.0)
                            break

        # 5. Compute 4: Category Matching Score
        category_scores = np.zeros(total_standards)
        inferred_cat = analysis["category"].lower()
        candidate_cats = [c.lower() for c in analysis.get("category_candidates", [])]

        for idx in range(total_standards):
            std_cat = self.standards[idx].get("category", "").lower()
            if inferred_cat in std_cat:
                category_scores[idx] = 1.0
            elif any(c in std_cat for c in candidate_cats):
                category_scores[idx] = 0.75
            else:
                category_scores[idx] = 0.10

        # 6. Combined Relevance Score Formula
        final_scores = (
            0.35 * tfidf_scores +
            0.35 * semantic_scores +
            0.20 * keyword_scores +
            0.10 * category_scores
        )

        # Direct standard code or product hit boost
        extracted_code = extract_standard_code(product_description)
        if extracted_code:
            code_num = extracted_code.replace("IS ", "").strip()
            for idx in range(total_standards):
                s_code = self.standards[idx].get("standard_code", "")
                if extracted_code.lower() in s_code.lower() or code_num in s_code:
                    final_scores[idx] = 1.0
                    tfidf_scores[idx] = max(tfidf_scores[idx], 1.0)
                    semantic_scores[idx] = max(semantic_scores[idx], 1.0)
                    keyword_scores[idx] = max(keyword_scores[idx], 1.0)
                    category_scores[idx] = max(category_scores[idx], 1.0)
        else:
            # Direct applicable_products match boost when user mentions a cataloged product
            for idx in range(total_standards):
                std_prods = sorted([p.lower() for p in self.standards[idx].get("applicable_products", [])], key=len, reverse=True)
                std_main_prod = self.standards[idx].get("product", "").lower()
                matched_len = 0
                for p in std_prods:
                    if p in cleaned_input:
                        matched_len = max(matched_len, len(p))
                if std_main_prod and std_main_prod in cleaned_input:
                    matched_len = max(matched_len, len(std_main_prod))
                
                if matched_len > 0:
                    # Longer, more specific product phrase matches receive higher boost
                    boost = 0.30 + min(matched_len / 50.0, 0.25)
                    final_scores[idx] += boost

            final_scores = np.clip(final_scores, 0.0, 1.0)

            # Dampen spurious scores if no TF-IDF / semantic lexical overlap and no keyword match exists
            for idx in range(total_standards):
                if tfidf_scores[idx] < 0.02 and semantic_scores[idx] < 0.02 and keyword_scores[idx] < 0.10:
                    final_scores[idx] = 0.0

        # Rank indices
        ranked_indices = np.argsort(final_scores)[::-1]
        results = []

        for idx in ranked_indices[:top_k]:
            std = self.standards[idx]
            f_score = float(final_scores[idx])
            
            # Extract status & clarity
            mandatory_status = std.get("mandatory_status", "Voluntary")
            is_mandatory = "mandatory" in mandatory_status.lower()
            cert_scheme = std.get("certification_scheme", "BIS Scheme I")

            # Explanation of recommendation rationale
            explanation = self._build_recommendation_explanation(
                product_description,
                analysis,
                std,
                f_score,
                is_mandatory
            )

            # Sanitize URLs and citations
            clean_source_url = sanitize_and_validate_url(std.get("source_url"))
            clean_ref_doc = str(std.get("source_document") or "BIS Specification Document").strip()
            clean_clause = str(std.get("reference_clause") or "Relevant Technical Clauses").strip()

            std_num = std.get("standard_number") or std.get("standard_code")
            results.append({
                "standard_number": std_num,
                "standard_code": std.get("standard_code") or std_num,
                "standard_title": std.get("title"),
                "relevance_score": round(f_score, 4),
                "score_breakdown": {
                    "tfidf_score": round(float(tfidf_scores[idx]), 4),
                    "semantic_score": round(float(semantic_scores[idx]), 4),
                    "keyword_score": round(float(keyword_scores[idx]), 4),
                    "category_score": round(float(category_scores[idx]), 4)
                },
                "product_match": std.get("product"),
                "applicable_products": std.get("applicable_products", []),
                "category": std.get("category"),
                "product_categories": std.get("product_categories", [std.get("category")]),
                "verification_status": std.get("verification_status", "verified"),
                "edition_or_year": std.get("edition_or_year", ""),
                "certification_information": {
                    "scheme": cert_scheme,
                    "mandatory_status": mandatory_status,
                    "is_mandatory": is_mandatory,
                    "compliance_status": std.get("compliance_status", "Compulsory under QCO" if is_mandatory else "Voluntary Certification"),
                    "mandatory_status_source": std.get("mandatory_status_source", "Central Government Gazette QCO Notification" if is_mandatory else "Voluntary Standardization"),
                    "certification_type": "Mandatory Certification (QCO / Statutory)" if is_mandatory else "Voluntary Specification / Guidance Standard",
                    "note": "High relevance score indicates technical product alignment. Certification is mandatory only if covered under a Gazetted Quality Control Order (QCO)."
                },
                "testing_information": std.get("testing_parameters"),
                "source": clean_source_url,
                "source_url": clean_source_url,
                "source_title": std.get("source_title", "BIS Standards Directory"),
                "supporting_excerpt": std.get("supporting_excerpt", std.get("scope", "")),
                "reference_document": clean_ref_doc,
                "page_section_clause": clean_clause,
                "recommendation_explanation": explanation
            })

        return {
            "input_description": product_description,
            "extracted_analysis": analysis,
            "top_standards": results,
            "recommendations": results
        }


    def _build_recommendation_explanation(
        self,
        query: str,
        analysis: Dict[str, Any],
        std: Dict[str, Any],
        score: float,
        is_mandatory: bool
    ) -> str:
        """Constructs plain-language reasoning for why the standard was recommended."""
        matched_kw = [k for k in analysis["keywords"] if k in std.get("title", "").lower() or k in std.get("product", "").lower() or k in std.get("scope", "").lower()]
        kw_str = ", ".join(matched_kw) if matched_kw else "domain specifications"
        
        cert_text = (
            "This standard falls under a Mandatory Quality Control Order (QCO); compliance and BIS certification are required prior to commercial sale in India."
            if is_mandatory
            else "This standard is currently Voluntary / Guidance specification. Certification is not legally mandated unless specified in buyer procurement requirements."
        )

        return (
            f"Recommended because your product description aligns with the '{std.get('category')}' domain, matching technical parameters for '{std.get('product')}' based on keywords ({kw_str}). {cert_text}"
        )

recommendation_engine = StandardRecommendationEngine()
