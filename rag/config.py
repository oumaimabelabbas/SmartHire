"""Configuration du service RAG"""
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

class Settings:
    """Paramètres de configuration"""

    # FastAPI
    APP_NAME: str = "SmartHire RAG Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Ports et URLs
    RAG_SERVICE_PORT: int = 8000
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8086")

    # LLM Configuration
    # Gemini est le fournisseur LLM principal du projet.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_BASE_URL: str = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    GEMINI_TIMEOUT_SECONDS: int = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "30"))

    # Embeddings locaux pour éviter toute dépendance à une autre clé API.
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "hashing").lower()
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    USE_OLLAMA: bool = os.getenv("USE_OLLAMA", "false").lower() == "true"

    # RAG configuration
    CHUNK_SIZE_WORDS: int = int(os.getenv("CHUNK_SIZE_WORDS", "120"))
    CHUNK_OVERLAP_WORDS: int = int(os.getenv("CHUNK_OVERLAP_WORDS", "30"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))

    # Local persistence for structured skills and vectors
    DATA_DIR: str = os.getenv("RAG_DATA_DIR", "data")
    VECTOR_STORE_DIR: str = os.getenv("VECTOR_STORE_DIR", os.path.join(DATA_DIR, "vector_store_chroma"))
    SKILL_STORE_PATH: str = os.path.join(DATA_DIR, "skills_store.json")
    EMBEDDING_CACHE_PATH: str = os.path.join(DATA_DIR, "embedding_cache.json")

    # Scoring configuration
    MIN_SCORE: float = 0.0
    MAX_SCORE: float = 100.0


settings = Settings()
