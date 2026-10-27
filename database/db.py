import os
import json
import logging
from typing import List, Dict, Any, Optional
from config import Config

logger = logging.getLogger("bis_ai.database")

# In-memory document storage fallback when MongoDB daemon is not active
_MEMORY_DB: Dict[str, List[Dict[str, Any]]] = {
    "standards": [],
    "schemes": [],
    "laboratories": [],
    "faqs": [],
    "queries_log": []
}

class DatabaseManager:
    """
    Database Manager providing dual-mode persistence:
    1. Primary: MongoDB via PyMongo if connection is active.
    2. Resilient Fallback: Memory / JSON File storage if MongoDB server is offline.
    """
    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self._initialize_connection()

    def _initialize_connection(self):
        try:
            from pymongo import MongoClient
            self.client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=1500)
            # Trigger quick ping
            self.client.admin.command('ping')
            self.db = self.client[Config.MONGODB_DB_NAME]
            self.is_connected = True
            logger.info("Successfully connected to live MongoDB database.")
        except Exception as e:
            self.is_connected = False
            logger.warning(f"MongoDB not reachable ({e}). Operating in memory/JSON resilient mode.")
            self._load_local_data_to_memory()

    def _load_local_data_to_memory(self):
        """Loads static JSON datasets into memory fallback store."""
        for name in ["standards", "schemes", "laboratories", "faqs"]:
            file_path = Config.DATA_DIR / f"{name}.json"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        _MEMORY_DB[name] = json.load(f)
                except Exception as ex:
                    logger.error(f"Error loading {file_path}: {ex}")

    def get_collection_data(self, collection_name: str) -> List[Dict[str, Any]]:
        """Returns all unique documents from MongoDB or in-memory fallback."""
        raw_docs = []
        if self.is_connected and self.db is not None:
            try:
                coll = self.db[collection_name]
                raw_docs = list(coll.find({}, {"_id": 0}))
            except Exception as e:
                logger.warning(f"Mongo fetch failed for {collection_name}: {e}. Falling back to memory.")
        
        if not raw_docs:
            if not _MEMORY_DB.get(collection_name):
                self._load_local_data_to_memory()
            raw_docs = _MEMORY_DB.get(collection_name, [])

        # Deduplicate by 'id'
        seen_ids = set()
        unique_docs = []
        for d in raw_docs:
            doc_id = d.get("id") or d.get("standard_code") or d.get("scheme_name") or d.get("lab_name") or str(d)
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_docs.append(d)
        return unique_docs

    def insert_document(self, collection_name: str, doc: Dict[str, Any]):
        """Inserts a single document into MongoDB and in-memory cache without duplicates."""
        doc_copy = {k: v for k, v in doc.items() if k != "_id"}
        if self.is_connected and self.db is not None:
            try:
                self.db[collection_name].insert_one(doc_copy.copy())
            except Exception as e:
                logger.debug(f"Mongo insert: {e}")
        
        if collection_name not in _MEMORY_DB:
            _MEMORY_DB[collection_name] = []
        # Prevent in-memory duplicates
        if doc_copy not in _MEMORY_DB[collection_name]:
            _MEMORY_DB[collection_name].append(doc_copy)

    def update_document(self, collection_name: str, query: Dict[str, Any], update_fields: Dict[str, Any]) -> bool:
        """Updates a document in MongoDB and in-memory cache matching query."""
        updated = False
        doc_id = query.get("id") or query.get("standard_code")

        if self.is_connected and self.db is not None:
            try:
                coll = self.db[collection_name]
                res = coll.update_one(query, {"$set": update_fields})
                if res.matched_count > 0:
                    updated = True
            except Exception as e:
                logger.warning(f"Mongo update error: {e}")

        mem_list = _MEMORY_DB.get(collection_name, [])
        for item in mem_list:
            match = False
            if doc_id and (item.get("id") == doc_id or item.get("standard_code") == doc_id):
                match = True
            elif all(item.get(k) == v for k, v in query.items()):
                match = True
            if match:
                item.update(update_fields)
                updated = True
                break

        return updated

    def delete_document(self, collection_name: str, query: Dict[str, Any]) -> bool:
        """Deletes a document from MongoDB and in-memory cache matching query."""
        deleted = False
        doc_id = query.get("id") or query.get("standard_code")

        if self.is_connected and self.db is not None:
            try:
                coll = self.db[collection_name]
                res = coll.delete_one(query)
                if res.deleted_count > 0:
                    deleted = True
            except Exception as e:
                logger.warning(f"Mongo delete error: {e}")

        if collection_name in _MEMORY_DB:
            original_len = len(_MEMORY_DB[collection_name])
            _MEMORY_DB[collection_name] = [
                item for item in _MEMORY_DB[collection_name]
                if not (
                    (doc_id and (item.get("id") == doc_id or item.get("standard_code") == doc_id)) or
                    all(item.get(k) == v for k, v in query.items())
                )
            ]
            if len(_MEMORY_DB[collection_name]) < original_len:
                deleted = True

        return deleted

    def log_query(self, query_record: Dict[str, Any]):
        """Log queries and audit records."""
        self.insert_document("queries_log", query_record)

    def get_status(self) -> Dict[str, Any]:
        return {
            "mongodb_connected": self.is_connected,
            "mode": "MongoDB" if self.is_connected else "In-Memory/File Resilient Cache",
            "standards_count": len(self.get_collection_data("standards")),
            "schemes_count": len(self.get_collection_data("schemes")),
            "laboratories_count": len(self.get_collection_data("laboratories")),
            "faqs_count": len(self.get_collection_data("faqs"))
        }

db_manager = DatabaseManager()
