import os
import sys
import logging
from pathlib import Path
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    VotingClassifier
)

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import Config
from ml.preprocessing import DataPreprocessor
from ml.evaluate_models import evaluate_classifier_models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bis_ai.train_intent_model")

def train_ensemble_pipeline():
    """
    Complete ML Pipeline:
    1. Loads data from data/training/intent_dataset.csv
    2. Cleans text & normalizes multilingual queries
    3. Train/test split with stratification
    4. Label encoding
    5. TF-IDF feature extraction
    6. Trains:
       - Random Forest
       - Extra Trees
       - Gradient Boosting
       - VotingClassifier (soft voting ensemble)
    7. Evaluates and compares all models
    8. Saves best model and preprocessor using joblib
    """
    data_path = Config.BASE_DIR / "data" / "training" / "intent_dataset.csv"
    if not data_path.exists():
        data_path = Config.BASE_DIR / "data" / "intent_dataset.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Training dataset not found at {data_path}")

    logger.info(f"Loading dataset from {data_path}...")
    preprocessor = DataPreprocessor(max_features=1500, ngram_range=(1, 2))
    df = preprocessor.load_data(str(data_path))

    queries, labels = preprocessor.preprocess_dataframe(df)
    unique_labels = sorted(list(set(labels)))
    logger.info(f"Loaded {len(queries)} samples across {len(unique_labels)} intent classes: {unique_labels}")

    # Train / Test split with stratification
    X_train_raw, X_test_raw, y_train_raw, y_test_raw = train_test_split(
        queries, labels, test_size=0.20, random_state=42, stratify=labels
    )

    # Feature extraction & label encoding
    X_train, y_train = preprocessor.fit_transform(X_train_raw, y_train_raw)
    X_test = preprocessor.transform(X_test_raw)
    y_test = preprocessor.label_encoder.transform(y_test_raw)

    class_names = list(preprocessor.label_encoder.classes_)

    # 1. Random Forest Classifier
    rf = RandomForestClassifier(
        n_estimators=120,
        max_depth=14,
        min_samples_split=2,
        random_state=42
    )

    # 2. Extra Trees Classifier
    et = ExtraTreesClassifier(
        n_estimators=120,
        max_depth=14,
        min_samples_split=2,
        random_state=42
    )

    # 3. Gradient Boosting Classifier
    gb = GradientBoostingClassifier(
        n_estimators=80,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )

    # 4. Ensemble: VotingClassifier (Soft voting)
    ensemble = VotingClassifier(
        estimators=[
            ('rf', rf),
            ('et', et),
            ('gb', gb)
        ],
        voting='soft'
    )

    logger.info("Training individual and ensemble models...")
    rf.fit(X_train, y_train)
    et.fit(X_train, y_train)
    gb.fit(X_train, y_train)
    ensemble.fit(X_train, y_train)

    models_dict = {
        "Random Forest": rf,
        "Extra Trees": et,
        "Gradient Boosting": gb,
        "Voting Ensemble": ensemble
    }

    # Evaluate models
    logger.info("Evaluating models and generating metrics...")
    eval_results = evaluate_classifier_models(
        models_dict,
        X_test,
        y_test,
        class_names
    )

    # Save best model using joblib
    Config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    best_model_path = Config.MODELS_DIR / "ensemble_classifier.joblib"
    preprocessor_path = Config.MODELS_DIR / "preprocessor.joblib"

    joblib.dump(ensemble, best_model_path)
    joblib.dump(preprocessor, preprocessor_path)

    # Also save vectorizer separately for backward compatibility
    joblib.dump(preprocessor.vectorizer, Config.MODELS_DIR / "tfidf_vectorizer.joblib")

    logger.info(f"Ensemble model saved to: {best_model_path}")
    logger.info(f"Preprocessor saved to: {preprocessor_path}")

    # Print Comparison Table
    comparison_table = eval_results["comparison_table"]
    print("\n" + "=" * 65)
    print("      MODEL COMPARISON TABLE - BIS INTENT CLASSIFICATION")
    print("=" * 65)
    for row in comparison_table:
        print(f"{row['Model']:<20} | Acc: {row['Accuracy']:<8} | Prec: {row['Precision']:<8} | Rec: {row['Recall']:<8} | Macro F1: {row['Macro F1']:<8} | Weighted F1: {row['Weighted F1']:<8}")
    print("=" * 65 + "\n")

    return eval_results

if __name__ == "__main__":
    train_ensemble_pipeline()
