import re
import string
from typing import List, Tuple
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from services.multilingual import MultilingualService

def clean_query_text(text: str) -> str:
    """
    Cleans raw query text, normalizes multilingual tokens to domain keywords,
    strips punctuation and compresses extra whitespace.
    """
    if not isinstance(text, str) or not text.strip():
        return ""
    
    # 1. Multilingual processing
    multi_res = MultilingualService.process_query(text)
    normalized = multi_res["normalized_query"]

    # 2. Text normalization
    normalized = normalized.lower().strip()
    normalized = re.sub(r'[\r\n\t]+', ' ', normalized)
    normalized = re.sub(r'[^\w\s\-]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

class DataPreprocessor:
    """
    Handles data loading, cleaning, train/test splitting, label encoding,
    and TF-IDF feature extraction.
    """

    def __init__(self, max_features: int = 1500, ngram_range: Tuple[int, int] = (1, 2)):
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            sublinear_tf=True
        )
        self.label_encoder = LabelEncoder()
        self.is_fitted = False

    def load_data(self, csv_path: str) -> pd.DataFrame:
        """Loads and verifies intent_dataset.csv."""
        df = pd.read_csv(csv_path)
        required = ["query_text", "intent"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' missing from {csv_path}")
        return df

    def preprocess_dataframe(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """Cleans queries and extracts intent labels."""
        cleaned_queries = [clean_query_text(q) for q in df["query_text"]]
        intents = [str(i).strip() for i in df["intent"]]
        return cleaned_queries, intents

    def fit_transform(self, texts: List[str], labels: List[str]):
        """Fits vectorizer and label encoder on training texts and labels."""
        X = self.vectorizer.fit_transform(texts)
        y = self.label_encoder.fit_transform(labels)
        self.is_fitted = True
        return X, y

    def transform(self, texts: List[str]):
        """Transforms unseen texts using fitted vectorizer."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted before transforming.")
        return self.vectorizer.transform(texts)

    def inverse_transform_labels(self, y_indices) -> List[str]:
        """Maps numeric class indices back to intent label strings."""
        return self.label_encoder.inverse_transform(y_indices)
