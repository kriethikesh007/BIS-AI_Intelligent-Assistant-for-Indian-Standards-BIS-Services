import logging
import joblib
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
from config import Config
from utils.text_cleaner import clean_text

logger = logging.getLogger("bis_ai.classifier")

class IntentClassifierService:
    """
    Ensemble Intent Classifier encapsulating VotingClassifier (RF + Extra Trees + Gradient Boosting).
    Classifies queries into:
    - STANDARD_RECOMMENDATION
    - STANDARD_INFORMATION
    - CERTIFICATION
    - HALLMARKING
    - LABORATORY
    - CONSUMER
    - GENERAL_BIS
    - OTHER
    """

    def __init__(self):
        self.model = None
        self.vectorizer = None
        self._load_model()

    def _load_model(self):
        model_path = Config.MODELS_DIR / "ensemble_classifier.joblib"
        vec_path = Config.MODELS_DIR / "tfidf_vectorizer.joblib"

        if model_path.exists() and vec_path.exists():
            try:
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vec_path)
                logger.info("Ensemble Intent Classifier loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load ensemble classifier: {e}")
        else:
            logger.warning("Ensemble classifier artifacts not found. Rule-based fallback active until trained.")

    def predict(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Predicts intent class with probability confidence score.
        Returns (predicted_intent, confidence, all_probabilities).
        """
        from ml.predict_intent import predict_intent
        res = predict_intent(text)
        intent = res["intent"]
        conf = res["confidence"]
        return intent, conf, {intent: conf}

intent_classifier = IntentClassifierService()
