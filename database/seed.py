import os
import json
import logging
from pathlib import Path
import sys

# Ensure root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import Config
from database.db import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bis_ai.seed")

def ingest_all():
    """Ingests standards, schemes, laboratories, and FAQs into the database."""
    logger.info("Starting BIS Knowledge Base ingestion...")
    collections = ["standards", "schemes", "laboratories", "faqs"]
    total = 0

    for col in collections:
        file_path = Config.DATA_DIR / f"{col}.json"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        logger.info(f"Ingesting {len(items)} records into '{col}'...")
        if db_manager.is_connected and db_manager.db is not None:
            # Clear existing to ensure freshness
            db_manager.db[col].delete_many({})
            if items:
                db_manager.db[col].insert_many(items)
        
        # Also ensure memory db has it (reset collection first to prevent stale records)
        from database.db import _MEMORY_DB
        _MEMORY_DB[col] = []
        for item in items:
            db_manager.insert_document(col, item)
        total += len(items)

    status = db_manager.get_status()
    logger.info(f"Ingestion completed. Total documents: {total}. Status: {status}")
    return total

if __name__ == "__main__":
    ingest_all()
