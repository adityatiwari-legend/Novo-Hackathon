import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic AI Co-Pilot for GxP IT System Management"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "gxp-secret-key-novo-hackathon-2026-audit-ready-secure")
    
    # OpenRouter AI Provider Configuration (Default)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    # Generic AI Model Settings (Conservative for GxP Compliance)
    AI_MODEL: str = os.getenv("AI_MODEL", os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.1"))
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "2048"))
    
    # Embedding Configuration
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "local")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Legacy / Secondary OpenAI compatibility (Optional)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./gxp_copilot.db")
    
    # Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    WORKSPACE_ROOT: str = os.path.dirname(BASE_DIR)
    DATA_DIR: str = os.path.join(WORKSPACE_ROOT, "data")
    UPLOAD_DIR: str = os.path.join(DATA_DIR, "uploads")
    VECTOR_STORE_PATH: str = os.path.join(DATA_DIR, "vector_store")
    SEED_DIR: str = os.path.join(DATA_DIR, "seed")
    MOCK_ENTERPRISE_DIR: str = os.path.join(DATA_DIR, "mock_enterprise")
    SAMPLE_DOCS_DIR: str = os.path.join(DATA_DIR, "sample_documents")
    
    # Flags & Mocks
    DEMO_MODE: bool = True
    MOCK_SERVICENOW: bool = True
    MOCK_VAULT: bool = True
    MOCK_IAM: bool = True
    MOCK_MONITORING: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
os.makedirs(settings.SEED_DIR, exist_ok=True)
os.makedirs(settings.SAMPLE_DOCS_DIR, exist_ok=True)
os.makedirs(settings.MOCK_ENTERPRISE_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.DATA_DIR, "evidence_packs"), exist_ok=True)
os.makedirs(os.path.join(settings.DATA_DIR, "drafts"), exist_ok=True)
