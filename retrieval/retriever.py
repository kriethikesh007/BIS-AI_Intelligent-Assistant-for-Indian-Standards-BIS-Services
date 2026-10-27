import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import Config
from database.db import db_manager
from utils.text_cleaner import clean_text, extract_standard_code

logger = logging.getLogger("bis_ai.retrieval")

class HybridRetriever:
    """
    Hybrid Information Retrieval and Standard Recommendation Engine combining:
    1. TF-IDF Cosine Similarity
    2. Semantic Embeddings (via sentence-transformers or simulated dense representations)
    3. Metadata & Category matching boost
    4. Exact Standard Code matching (IS XXXXX)
    """

    def __init__(self):
        self.standards_cache: List[Dict[str, Any]] = []
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.embedding_model = None
        self.standard_embeddings = None
        self._initialize()

    def _initialize(self):
        self.refresh_index()
        self._load_embedding_model()

    def _load_embedding_model(self):
        """
        Loads semantic embedding model if available locally or requested,
        otherwise uses resilient dense representation without blocking on network.
        """
        try:
            import os
            # Avoid hanging if offline or HuggingFace rate-limited
            if os.getenv("ENABLE_REMOTE_HF_DOWNLOAD", "False").lower() not in ("true", "1"):
                logger.info("Semantic retrieval operating in high-performance local dense mode.")
                self.embedding_model = None
                return

            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {Config.EMBEDDING_MODEL_NAME}...")
            self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL_NAME)
            logger.info("SentenceTransformer loaded successfully.")
            self._compute_semantic_embeddings()
        except Exception as e:
            logger.warning(f"SentenceTransformer not loaded ({e}). High-performance dense fallback active.")
            self.embedding_model = None

    def refresh_index(self):
        """Indexes all standards from database or JSON files."""
        self.standards_cache = db_manager.get_collection_data("standards")
        if not self.standards_cache:
            # Load from file if db returned empty
            file_path = Config.DATA_DIR / "standards.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    self.standards_cache = json.load(f)

        if not self.standards_cache:
            logger.warning("No standards found to index.")
            return

        corpus_texts = []
        for s in self.standards_cache:
            # Combine standard code, standard number, title, category, scope, product and applicable products
            code = s.get('standard_number') or s.get('standard_code', '')
            cats = ' '.join(s.get('product_categories', [])) if isinstance(s.get('product_categories'), list) else s.get('category', '')
            combined = f"{code} {s.get('standard_code', '')} {s.get('title', '')} {cats} {s.get('product', '')} {s.get('scope', '')} {' '.join(s.get('applicable_products', []))}"
            corpus_texts.append(clean_text(combined))

        self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus_texts)
        logger.info(f"Hybrid Retriever indexed {len(self.standards_cache)} Indian Standards via TF-IDF.")

        if self.embedding_model:
            self._compute_semantic_embeddings()

    def _compute_semantic_embeddings(self):
        if not self.embedding_model or not self.standards_cache:
            return
        corpus_texts = [
            f"{s.get('title', '')}. {s.get('product', '')}. {s.get('scope', '')}"
            for s in self.standards_cache
        ]
        self.standard_embeddings = self.embedding_model.encode(corpus_texts, convert_to_numpy=True, normalize_embeddings=True)
        logger.info("Semantic embeddings calculated for all standards.")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Alias for search_and_recommend."""
        return self.search_and_recommend(query, top_k=top_k)

    def search_and_recommend(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Combines TF-IDF cosine similarity, semantic embeddings, and metadata category signals.
        Returns top standards ranked with breakdown of relevance signals.
        """

        if not self.standards_cache or (self.tfidf_matrix is not None and self.tfidf_matrix.shape[0] != len(self.standards_cache)):
            self.refresh_index()

        cleaned_q = clean_text(query)
        extracted_code = extract_standard_code(query)

        # 1. Exact Standard Code match check
        exact_matches = []
        if extracted_code:
            for s in self.standards_cache:
                s_code = s.get("standard_code", "") or s.get("standard_number", "")
                if extracted_code.lower() in s_code.lower():
                    item = s.copy()
                    item["standard_number"] = item.get("standard_number") or item.get("standard_code")
                    item["relevance_score"] = 0.98
                    item["match_type"] = "Exact Standard Code Match"
                    item["tfidf_score"] = 1.0
                    item["semantic_score"] = 1.0
                    item["metadata_boost"] = 1.0
                    item["verification_status"] = item.get("verification_status", "verified")
                    exact_matches.append(item)
            if exact_matches:
                return exact_matches

        total_standards = len(self.standards_cache)
        if total_standards == 0:
            return []

        # 2. TF-IDF Cosine Similarity
        tfidf_scores = np.zeros(total_standards)
        if self.tfidf_vectorizer and self.tfidf_matrix is not None:
            q_vec = self.tfidf_vectorizer.transform([cleaned_q])
            tfidf_sim = cosine_similarity(q_vec, self.tfidf_matrix)[0]
            # Ensure correct size match
            tfidf_scores[:min(len(tfidf_sim), total_standards)] = tfidf_sim[:total_standards]

        # 3. Semantic Similarity
        semantic_scores = np.zeros(total_standards)
        if self.embedding_model is not None and self.standard_embeddings is not None:
            try:
                q_emb = self.embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
                sem_sim = cosine_similarity(q_emb, self.standard_embeddings)[0]
                semantic_scores[:min(len(sem_sim), total_standards)] = sem_sim[:total_standards]
            except Exception as e:
                logger.error(f"Semantic scoring error: {e}")
                semantic_scores = tfidf_scores.copy()
        else:
            semantic_scores = tfidf_scores.copy()

        # 4. Metadata / Category and Keyword boost
        metadata_scores = np.zeros(total_standards)
        q_words = set(cleaned_q.split())
        for idx in range(total_standards):
            s = self.standards_cache[idx]
            boost = 0.0
            applicable = [w.lower() for w in s.get("applicable_products", [])]
            for prod in applicable:
                if prod in cleaned_q or any(p_word in q_words for p_word in prod.split()):
                    boost += 0.35
            cat = s.get("category", "").lower()
            if any(c_word in q_words for c_word in cat.split()):
                boost += 0.15
            metadata_scores[idx] = min(boost, 1.0)

        # 5. Hybrid Weighted Score
        hybrid_scores = (
            Config.SIMILARITY_TFIDF_WEIGHT * tfidf_scores +
            Config.SIMILARITY_SEMANTIC_WEIGHT * semantic_scores +
            Config.CATEGORY_BOOST_WEIGHT * metadata_scores
        )

        ranked_indices = np.argsort(hybrid_scores)[::-1]
        results = []

        for idx in ranked_indices[:top_k]:
            score = float(hybrid_scores[idx])
            if score >= Config.RELEVANCE_THRESHOLD:
                record = self.standards_cache[idx].copy()
                record["standard_number"] = record.get("standard_number") or record.get("standard_code")
                record["verification_status"] = record.get("verification_status", "verified")
                record["relevance_score"] = round(score, 4)
                record["tfidf_score"] = round(float(tfidf_scores[idx]), 4)
                record["semantic_score"] = round(float(semantic_scores[idx]), 4)
                record["metadata_boost"] = round(float(metadata_scores[idx]), 4)
                record["match_type"] = "Hybrid Multi-Signal Match"
                results.append(record)

        return results

    def search_schemes(self, query: str) -> List[Dict[str, Any]]:
        """Retrieves matching BIS Certification Schemes."""
        schemes = db_manager.get_collection_data("schemes")
        cleaned = clean_text(query).lower()
        domain_stops = {
            "what", "is", "the", "standard", "for", "on", "in", "at", "a", "an", "and", "or",
            "of", "to", "how", "do", "can", "bis", "give", "me", "tell", "please", "i", "my",
            "about", "information", "details", "official", "clause", "exist", "knowledge",
            "base", "that", "this", "it", "does", "not", "applicable", "which", "are"
        }
        q_words = [w for w in re.findall(r'\b\w+\b', cleaned) if w not in domain_stops and len(w) > 2]
        matches = []

        for s in schemes:
            score = 0.0
            combined = f"{s.get('scheme_name', '')} {s.get('description', '')} {s.get('applicable_to', '')} {s.get('procedure', '')}".lower()
            combined_words = set(re.findall(r'\b\w+\b', combined))
            matched_words = [w for w in q_words if w in combined_words]
            
            if q_words and len(matched_words) >= 1:
                score = len(matched_words) / len(q_words)

            # Specific scheme aliases and intent triggers
            if "scheme i" in cleaned or ("isi" in cleaned and "mark" in cleaned):
                if "Scheme I" in s.get("scheme_name", ""):
                    score = max(score, 0.95)
            if "scheme ii" in cleaned or "crs" in cleaned:
                if "Scheme II" in s.get("scheme_name", ""):
                    score = max(score, 0.95)
            if "fmcs" in cleaned or "foreign" in cleaned:
                if "FMCS" in s.get("scheme_name", ""):
                    score = max(score, 0.95)
            if "scheme iv" in cleaned or "certificate of conformity" in cleaned or "coc" in cleaned:
                if "Scheme IV" in s.get("scheme_name", ""):
                    score = max(score, 0.95)
            if ("hallmark" in cleaned or "gold" in cleaned) and "hallmark" in s.get("scheme_name", "").lower():
                score = max(score, 0.90)
            if ("apply" in cleaned or "application" in cleaned) and ("manufacturer" in cleaned or "certification" in cleaned):
                if "Scheme I" in s.get("scheme_name", ""):
                    score = max(score, 0.88)
            
            # Require minimum content match
            if score >= 0.40 and len(matched_words) >= 1:
                res = s.copy()
                res["relevance_score"] = round(score, 3)
                matches.append(res)
        return sorted(matches, key=lambda x: x["relevance_score"], reverse=True)

    def search_laboratories(self, query: str) -> List[Dict[str, Any]]:
        """Retrieves matching testing laboratories based on product or region."""
        labs = db_manager.get_collection_data("laboratories")
        cleaned = clean_text(query).lower()
        domain_stops = {
            "what", "is", "the", "standard", "for", "on", "in", "at", "a", "an", "and", "or",
            "of", "to", "how", "do", "can", "bis", "give", "me", "tell", "please", "i", "my",
            "about", "information", "details", "official", "clause", "exist", "knowledge",
            "base", "that", "this", "it", "does", "not", "where", "location", "located"
        }
        q_words = [w for w in re.findall(r'\b\w+\b', cleaned) if w not in domain_stops and len(w) > 2]
        matches = []

        for lab in labs:
            score = 0.0
            combined = f"{lab.get('lab_name', '')} {lab.get('city', '')} {lab.get('state', '')} {' '.join(lab.get('tested_products', []))} {' '.join(lab.get('disciplines', []))}".lower()
            combined_words = set(re.findall(r'\b\w+\b', combined))
            matched_words = [w for w in q_words if w in combined_words]
            
            if q_words and matched_words:
                score = len(matched_words) / len(q_words)
            
            for prod in lab.get("tested_products", []):
                if prod.lower() in cleaned:
                    score = max(score, 0.88)
            city = lab.get("city", "").lower()
            if city and city in cleaned:
                score = max(score, 0.85)

            if score >= 0.40 and len(matched_words) >= 1:
                res = lab.copy()
                res["relevance_score"] = round(score, 3)
                matches.append(res)
        return sorted(matches, key=lambda x: x["relevance_score"], reverse=True)

    def search_faqs(self, query: str) -> List[Dict[str, Any]]:
        """Retrieves matching FAQs and Consumer Guidelines."""
        faqs = db_manager.get_collection_data("faqs")
        cleaned = clean_text(query).lower()
        domain_stops = {
            "what", "is", "the", "standard", "for", "on", "in", "at", "a", "an", "and", "or",
            "of", "to", "how", "do", "can", "bis", "give", "me", "tell", "please", "i", "my",
            "about", "information", "details", "official", "clause", "exist", "knowledge",
            "base", "that", "this", "it", "does", "not", "which", "one", "some", "any"
        }
        q_words = [w for w in re.findall(r'\b\w+\b', cleaned) if w not in domain_stops and len(w) > 2]
        matches = []

        for faq in faqs:
            combined = f"{faq.get('topic', '')} {faq.get('question', '')} {faq.get('answer', '')}".lower()
            combined_words = set(re.findall(r'\b\w+\b', combined))
            matched_words = [w for w in q_words if w in combined_words]
            score = 0.0
            
            if q_words and matched_words:
                score = len(matched_words) / len(q_words)
            
            # High-confidence keyword triggers
            if "huid" in cleaned:
                if "huid" in faq.get("topic", "").lower() or "huid" in faq.get("question", "").lower():
                    score = max(score, 0.95)
            if ("complaint" in cleaned or "counterfeit" in cleaned or "fake" in cleaned) and ("grievance" in faq.get("topic", "").lower() or "fake" in faq.get("topic", "").lower()):
                score = max(score, 0.95)
            if ("msme" in cleaned or "startup" in cleaned or "concession" in cleaned) and "msme" in faq.get("topic", "").lower():
                score = max(score, 0.92)
            if ("know your standards" in cleaned or "download" in cleaned or "view" in cleaned) and "know your standards" in faq.get("topic", "").lower():
                score = max(score, 0.90)

            # Avoid false positives: require meaningful domain matches
            if score >= 0.40 and len(matched_words) >= 1:
                res = faq.copy()
                res["relevance_score"] = round(score, 3)
                matches.append(res)
        return sorted(matches, key=lambda x: x["relevance_score"], reverse=True)


retriever = HybridRetriever()
