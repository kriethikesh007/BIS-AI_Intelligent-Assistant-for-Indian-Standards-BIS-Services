import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import Config

logger = logging.getLogger("bis_ai.evaluate_models")

def evaluate_classifier_models(
    models_dict: Dict[str, Any],
    X_test,
    y_test,
    class_names: List[str]
) -> Dict[str, Any]:
    """
    Evaluates individual models and ensemble across:
    - Accuracy
    - Precision (Weighted)
    - Recall (Weighted)
    - F1-score (Weighted)
    - Macro F1
    - Weighted F1
    - Full classification report
    - Confusion matrix
    """
    results = {}
    comparison_table = []

    for name, model in models_dict.items():
        y_pred = model.predict(X_test)
        
        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
        rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
        f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
        f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
        cm = confusion_matrix(y_test, y_pred, labels=range(len(class_names))).tolist()
        report = classification_report(
            y_test,
            y_pred,
            target_names=class_names,
            output_dict=True,
            zero_division=0
        )

        model_eval = {
            "model_name": name,
            "accuracy": round(acc, 4),
            "precision_weighted": round(prec, 4),
            "recall_weighted": round(rec, 4),
            "f1_weighted": round(f1_weighted, 4),
            "f1_macro": round(f1_macro, 4),
            "confusion_matrix": cm,
            "classification_report": report
        }
        results[name] = model_eval

        comparison_table.append({
            "Model": name,
            "Accuracy": f"{acc * 100:.2f}%",
            "Precision": f"{prec * 100:.2f}%",
            "Recall": f"{rec * 100:.2f}%",
            "Macro F1": f"{f1_macro * 100:.2f}%",
            "Weighted F1": f"{f1_weighted * 100:.2f}%"
        })

    # Save comparison table to markdown
    docs_dir = Config.BASE_DIR / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    comparison_md_path = docs_dir / "model_comparison.md"
    with open(comparison_md_path, "w", encoding="utf-8") as f:
        f.write("# BIS-AI Ensemble Model Evaluation & Benchmark Comparison\n\n")
        f.write("| Model | Accuracy | Precision | Recall | Macro F1 | Weighted F1 |\n")
        f.write("|---|---|---|---|---|---|\n")
        for row in comparison_table:
            f.write(f"| {row['Model']} | {row['Accuracy']} | {row['Precision']} | {row['Recall']} | {row['Macro F1']} | {row['Weighted F1']} |\n")
        f.write("\n*Evaluation performed on stratified test set from `intent_dataset.csv`.*")

    output_payload = {
        "classes": class_names,
        "models": results,
        "comparison_table": comparison_table
    }

    # Save to models/
    out_json = Config.MODELS_DIR / "model_comparison.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    logger.info(f"Model comparison completed and saved to {out_json}")
    return output_payload
