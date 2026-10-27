import logging
import joblib
from pathlib import Path
from typing import Tuple, Any, Optional

from config import Config
from ml.preprocessing import clean_query_text

logger = logging.getLogger("bis_ai.model_loader")

class ModelLoader:
    """
    Singleton / Cached loader for the trained intent ensemble and preprocessors.
    """
    _instance = None

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.metadata = None
        self.load_artifacts()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ModelLoader()
        return cls._instance

    def load_artifacts(self):
        """Loads serialized voting classifier ensemble and preprocessor."""
        model_path = Config.MODELS_DIR / "ensemble_classifier.joblib"
        prep_path = Config.MODELS_DIR / "preprocessor.joblib"
        meta_path = Config.MODELS_DIR / "model_comparison.json"

        if model_path.exists() and prep_path.exists():
            try:
                self.model = joblib.load(model_path)
                self.preprocessor = joblib.load(prep_path)
                if meta_path.exists():
                    import json
                    with open(meta_path, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                logger.info("Successfully loaded VotingClassifier ensemble and Preprocessor.")
            except Exception as e:
                logger.error(f"Error loading model artifacts: {e}")
                self.model = None
                self.preprocessor = None
        else:
            logger.warning(f"Model artifacts not found at {model_path}. Train intent model first.")

    def is_ready(self) -> bool:
        """Returns True if model and preprocessor are successfully loaded."""
        return self.model is not None and self.preprocessor is not None

model_loader = ModelLoader.get_instance()

