import os
import json
import logging
import joblib
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix

import sys
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import Config
from utils.text_cleaner import clean_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bis_ai.ensemble_trainer")

def train_ensemble_model():
    """
    Trains the ensemble classifier using:
    1. Random Forest
    2. Extra Trees
    3. Gradient Boosting
    Ensembled via VotingClassifier (soft voting).
    Evaluates with accuracy, precision, recall, F1, and confusion matrix.
    Saves models and metrics to the models/ directory.
    """
    dataset_path = Config.DATA_DIR / "intent_dataset.json"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Training dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = [clean_text(item["text"]) for item in data]
    labels = [item["intent"] for item in data]

    unique_labels = sorted(list(set(labels)))
    logger.info(f"Loaded {len(texts)} samples across {len(unique_labels)} intent classes: {unique_labels}")

    # Split dataset with stratification
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )

    # TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=1200,
        sublinear_tf=True
    )
    X_train = vectorizer.fit_transform(X_train_raw)
    X_test = vectorizer.transform(X_test_raw)

    # Individual Classifiers
    rf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    et = ExtraTreesClassifier(n_estimators=100, max_depth=12, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=75, learning_rate=0.1, max_depth=4, random_state=42)

    # Soft Voting Ensemble
    ensemble = VotingClassifier(
        estimators=[
            ('rf', rf),
            ('et', et),
            ('gb', gb)
        ],
        voting='soft'
    )

    logger.info("Training Voting Classifier ensemble (RF + ET + GB)...")
    ensemble.fit(X_train, y_train)

    # Predictions & Evaluation
    y_pred = ensemble.predict(X_test)
    y_prob = ensemble.predict_proba(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=ensemble.classes_).tolist()
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    # Evaluate individual models for architectural comparison
    rf.fit(X_train, y_train)
    rf_acc = float(accuracy_score(y_test, rf.predict(X_test)))
    et.fit(X_train, y_train)
    et_acc = float(accuracy_score(y_test, et.predict(X_test)))
    gb.fit(X_train, y_train)
    gb_acc = float(accuracy_score(y_test, gb.predict(X_test)))

    evaluation_results = {
        "ensemble_accuracy": acc,
        "ensemble_precision_weighted": float(prec),
        "ensemble_recall_weighted": float(rec),
        "ensemble_f1_weighted": float(f1),
        "individual_models": {
            "random_forest_accuracy": rf_acc,
            "extra_trees_accuracy": et_acc,
            "gradient_boosting_accuracy": gb_acc
        },
        "classes": list(ensemble.classes_),
        "confusion_matrix": cm,
        "detailed_classification_report": report_dict
    }

    logger.info(f"Model Training Succeeded! Ensemble Accuracy: {acc:.4f}, F1-score: {f1:.4f}")
    logger.info(f"RF Acc: {rf_acc:.4f}, ET Acc: {et_acc:.4f}, GB Acc: {gb_acc:.4f}")

    # Save artifacts
    os.makedirs(Config.MODELS_DIR, exist_ok=True)
    joblib.dump(ensemble, Config.MODELS_DIR / "ensemble_classifier.joblib")
    joblib.dump(vectorizer, Config.MODELS_DIR / "tfidf_vectorizer.joblib")
    
    with open(Config.MODELS_DIR / "evaluation_metrics.json", "w", encoding="utf-8") as f:
        json.dump(evaluation_results, f, indent=2)

    logger.info(f"Saved ensemble model and evaluation report to {Config.MODELS_DIR}")
    return evaluation_results

if __name__ == "__main__":
    train_ensemble_model()
