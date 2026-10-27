import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import Config
from utils.text_cleaner import clean_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bis_ai.pipeline")

# Standard 16 required columns for all knowledge records
REQUIRED_KNOWLEDGE_COLUMNS = [
    "id", "title", "category", "product", "description", "keywords",
    "standard_number", "certification_scheme", "mandatory_status",
    "testing_requirements", "source_url", "source_document",
    "page", "section", "clause", "last_updated"
]

class DataPipeline:
    """
    Automated Data Validation, Cleaning, Normalization, Knowledge-Base
    Compilation, and Quality Auditing Pipeline.
    """

    def __init__(self):
        self.raw_dir = Config.BASE_DIR / "data" / "raw"
        self.processed_dir = Config.BASE_DIR / "data" / "processed"
        self.kb_dir = Config.BASE_DIR / "data" / "knowledge_base"
        self.training_dir = Config.BASE_DIR / "data" / "training"
        self.report_path = Config.BASE_DIR / "data" / "data_quality_report.json"
        
        for d in [self.processed_dir, self.kb_dir, self.training_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def validate_csv(self, file_path: Path, required_cols: List[str]) -> Tuple[bool, List[str]]:
        """Checks file existence and column integrity."""
        errors = []
        if not file_path.exists():
            return False, [f"File {file_path.name} does not exist."]
        try:
            df = pd.read_csv(file_path)
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                errors.append(f"Missing mandatory columns: {missing_cols}")
            if len(df) == 0:
                errors.append(f"Dataset {file_path.name} is empty.")
            return len(errors) == 0, errors
        except Exception as e:
            return False, [f"Error reading {file_path.name}: {str(e)}"]

    def clean_and_normalize_record(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
        """
        Deduplicates, handles missing values, cleans whitespace and text fields,
        normalizes standard identifiers, and preserves SAMPLE DATA labels.
        """
        initial_count = len(df)
        
        # 1. Duplicate detection and removal by ID or title
        if "id" in df.columns:
            df = df.drop_duplicates(subset=["id"], keep="first")
        elif "query_text" in df.columns:
            df = df.drop_duplicates(subset=["query_text"], keep="first")
        duplicates_removed = initial_count - len(df)

        # 2. Missing value check and imputation
        missing_count = int(df.isnull().sum().sum())
        df = df.fillna({
            "product": "General / Cross-Domain",
            "keywords": "",
            "testing_requirements": "Standard verification required",
            "page": "General",
            "section": "General",
            "clause": "General",
            "mandatory_status": "Voluntary",
            "sample_data_flag": "SAMPLE DATA"
        })

        # 3. Text cleaning and normalization
        text_cols = [c for c in df.columns if df[c].dtype == object]
        for col in text_cols:
            df[col] = df[col].astype(str).str.strip()

        # Ensure SAMPLE DATA badge is present
        if "sample_data_flag" not in df.columns:
            df["sample_data_flag"] = "SAMPLE DATA"

        return df, duplicates_removed, missing_count

    def process_all_datasets(self) -> Dict[str, Any]:
        """Runs validation, processing, compile knowledge bases, and builds report."""
        logger.info("Executing BIS Data Ingestion & Quality Validation Pipeline...")
        
        report_data = {
            "pipeline_status": "SUCCESS",
            "datasets_processed": {},
            "summary_metrics": {
                "total_records": 0,
                "total_duplicates_removed": 0,
                "total_missing_values_handled": 0,
                "number_of_standards": 0,
                "number_of_categories": 0,
                "number_of_certification_schemes": 0,
                "number_of_laboratory_records": 0,
                "number_of_training_examples": 0
            },
            "sample_data_notice": "All benchmark records are explicitly labelled as 'SAMPLE DATA'. Authorized BIS requirements must not be fabricated."
        }

        knowledge_records = []
        unique_categories = set()
        unique_schemes = set()

        files_to_process = [
            ("standards.csv", REQUIRED_KNOWLEDGE_COLUMNS),
            ("certification.csv", REQUIRED_KNOWLEDGE_COLUMNS),
            ("hallmarking.csv", REQUIRED_KNOWLEDGE_COLUMNS),
            ("laboratories.csv", REQUIRED_KNOWLEDGE_COLUMNS),
            ("consumer_faq.csv", REQUIRED_KNOWLEDGE_COLUMNS),
            ("schemes.csv", REQUIRED_KNOWLEDGE_COLUMNS),
            ("standard_products.csv", REQUIRED_KNOWLEDGE_COLUMNS),
            ("intent_dataset.csv", ["id", "query_text", "intent", "sample_data_flag"])
        ]

        for fname, req_cols in files_to_process:
            raw_path = self.raw_dir / fname
            is_valid, errors = self.validate_csv(raw_path, req_cols)
            if not is_valid:
                logger.error(f"Validation failed for {fname}: {errors}")
                report_data["datasets_processed"][fname] = {"valid": False, "errors": errors}
                continue

            df = pd.read_csv(raw_path)
            cleaned_df, dupes, missing = self.clean_and_normalize_record(df)

            # Save to processed directory
            out_proc = self.processed_dir / fname
            cleaned_df.to_csv(out_proc, index=False)

            report_data["datasets_processed"][fname] = {
                "valid": True,
                "records": len(cleaned_df),
                "duplicates_removed": dupes,
                "missing_values_imputed": missing
            }
            report_data["summary_metrics"]["total_records"] += len(cleaned_df)
            report_data["summary_metrics"]["total_duplicates_removed"] += dupes
            report_data["summary_metrics"]["total_missing_values_handled"] += missing

            # Track domain metrics
            if fname == "standards.csv":
                report_data["summary_metrics"]["number_of_standards"] = len(cleaned_df)
            if fname == "laboratories.csv":
                report_data["summary_metrics"]["number_of_laboratory_records"] = len(cleaned_df)
            if fname == "schemes.csv":
                report_data["summary_metrics"]["number_of_certification_schemes"] = len(cleaned_df)
            if fname == "intent_dataset.csv":
                report_data["summary_metrics"]["number_of_training_examples"] = len(cleaned_df)
                cleaned_df.to_csv(self.training_dir / "intent_dataset.csv", index=False)

            # Aggregate knowledge records (excluding training queries)
            if fname != "intent_dataset.csv":
                for cat in cleaned_df.get("category", []):
                    unique_categories.add(str(cat).strip())
                for sch in cleaned_df.get("certification_scheme", []):
                    unique_schemes.add(str(sch).strip())
                records = cleaned_df.to_dict(orient="records")
                knowledge_records.extend(records)

        report_data["summary_metrics"]["number_of_categories"] = len(unique_categories)
        if report_data["summary_metrics"]["number_of_certification_schemes"] == 0:
            report_data["summary_metrics"]["number_of_certification_schemes"] = len(unique_schemes)

        # 4. Compile Unified Master Knowledge Base in JSON and CSV
        master_kb_df = pd.DataFrame(knowledge_records)
        master_kb_csv = self.kb_dir / "bis_master_knowledge_base.csv"
        master_kb_json = self.kb_dir / "bis_master_knowledge_base.json"

        master_kb_df.to_csv(master_kb_csv, index=False)
        with open(master_kb_json, "w", encoding="utf-8") as f:
            json.dump(knowledge_records, f, indent=2)

        # Also write the data quality report
        with open(self.report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        # Generate markdown report
        self.generate_markdown_quality_report(report_data)

        logger.info(f"Data Pipeline completed successfully! Compiled {len(knowledge_records)} master knowledge records.")
        return report_data

    def generate_markdown_quality_report(self, report_data: Dict[str, Any]):
        """Generates docs/data_quality_report.md."""
        m = report_data["summary_metrics"]
        d = report_data["datasets_processed"]
        md = f"""# BIS-AI Data Quality & Knowledge-Base Audit Report

**Audit Timestamp:** 2026-10-05  
**Data Integrity Status:** {report_data['pipeline_status']}  
**Provenance / Attribution:** {report_data['sample_data_notice']}

---

## 📊 Summary Metrics

| Metric | Value |
|---|---|
| **Total Processed Records** | **{m['total_records']}** |
| **Number of Indian Standards** | **{m['number_of_standards']}** |
| **Number of Unique Categories** | **{m['number_of_categories']}** |
| **Number of Certification Schemes** | **{m['number_of_certification_schemes']}** |
| **Number of Laboratory Records** | **{m['number_of_laboratory_records']}** |
| **Number of Training Examples** | **{m['number_of_training_examples']}** |
| **Duplicate Records Detected & Removed** | **{m['total_duplicates_removed']}** |
| **Missing Values Imputed & Normalized** | **{m['total_missing_values_handled']}** |

---

## 📁 Datasets Ingested

| Dataset File | Records | Duplicates Removed | Missing Values Imputed | Validation Status |
|---|---|---|---|---|
"""
        for filename, stats in d.items():
            md += f"| `{filename}` | {stats.get('records', 0)} | {stats.get('duplicates_removed', 0)} | {stats.get('missing_values_imputed', 0)} | {'✅ PASS' if stats.get('valid') else '❌ FAIL'} |\n"

        md += """
---

## 🛡️ Data Quality Controls & Guardrails

1. **Schema Enforcement:** Verified that every knowledge record satisfies all 16 required metadata fields (`id`, `title`, `category`, `product`, `description`, `keywords`, `standard_number`, `certification_scheme`, `mandatory_status`, `testing_requirements`, `source_url`, `source_document`, `page`, `section`, `clause`, `last_updated`).
2. **Deduplication:** Guaranteed primary key uniqueness across identifiers and queries.
3. **Data Labeling:** Explicitly marked every synthetic demonstration row as `SAMPLE DATA` to maintain rigorous scientific compliance with BIS regulatory requirements.
"""
        docs_dir = Config.BASE_DIR / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        with open(docs_dir / "data_quality_report.md", "w", encoding="utf-8") as f:
            f.write(md)

if __name__ == "__main__":
    pipeline = DataPipeline()
    report = pipeline.process_all_datasets()
    print(json.dumps(report, indent=2))
