import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables if .env exists
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "bis_ai_secret_fallback_key")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))
    # Security & Admin Configuration
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "bis_admin_secret_key_2026").strip()

    # CORS configuration
    CORS_ORIGINS = [
        o.strip() for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5000,http://127.0.0.1:5000"
        ).split(",") if o.strip()
    ]

    # Grok (xAI) & LLM Configuration
    # Supports GROK_API_KEY (official xAI docs: https://docs.x.ai/) with backward compatibility for GROQ_API_KEY
    GROK_API_KEY = os.getenv("GROK_API_KEY", "").strip() or os.getenv("XAI_API_KEY", "").strip() or os.getenv("GROQ_API_KEY", "").strip()
    GROK_BASE_URL = os.getenv("GROK_BASE_URL", os.getenv("GROK_API_BASE_URL", "")).strip()
    GROK_MODEL = os.getenv("GROK_MODEL", os.getenv("GROQ_MODEL", "")).strip()
    GROK_TIMEOUT = float(os.getenv("GROK_TIMEOUT", os.getenv("GROQ_TIMEOUT", 20.0)))
    GROK_MAX_TOKENS = int(os.getenv("GROK_MAX_TOKENS", os.getenv("GROQ_MAX_TOKENS", 1000)))
    GROK_TEMPERATURE = float(os.getenv("GROK_TEMPERATURE", os.getenv("GROQ_TEMPERATURE", 0.2)))

    # Backward compatibility aliases for existing modules
    GROQ_API_KEY = GROK_API_KEY
    GROQ_MODEL = GROK_MODEL or "grok-2-latest"
    GROQ_TIMEOUT = GROK_TIMEOUT
    GROQ_MAX_TOKENS = GROK_MAX_TOKENS
    GROQ_TEMPERATURE = GROK_TEMPERATURE

    # MongoDB Settings
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "bis_ai_db")

    # Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    DOCS_DIR = BASE_DIR / "docs"

    # ML & Retrieval weights
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", 0.32))
    SIMILARITY_TFIDF_WEIGHT = float(os.getenv("SIMILARITY_TFIDF_WEIGHT", 0.45))
    SIMILARITY_SEMANTIC_WEIGHT = float(os.getenv("SIMILARITY_SEMANTIC_WEIGHT", 0.45))
    CATEGORY_BOOST_WEIGHT = float(os.getenv("CATEGORY_BOOST_WEIGHT", 0.10))

    # Intents
    INTENT_CLASSES = [
        "STANDARD_RECOMMENDATION",
        "STANDARD_INFORMATION",
        "CERTIFICATION",
        "HALLMARKING",
        "LABORATORY",
        "CONSUMER",
        "GENERAL_BIS",
        "OTHER"
    ]
