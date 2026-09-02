import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR= Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

def _require(key:str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing Required env variable: {key}")
    return val

OPEN_API_KEY:str = _require("OPENAI_API_KEY")
OLLAMA_BASE_URL:str = _require("OLLAMA_BASE_URL")
PINECONE_KEY:str = _require("PINECONE_API_KEY")

PINECONE_INDEX_NAME:str = os.getenv("PINECONE_INDEX_NAME","medbot-gale")
PINECONE_ENVIRONMENT:str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

LLM_MODEL:str = os.getenv("LLM_MODEL", "qwen2:1.5b")
EMBEDDING_MODEL_NAME:str = os.getenv("EMBEDDING_MODEL_NAME", "NeuML/pubmedbert-base-embeddings")
EMBEDDING_DIMENSION:int = os.getenv("EMBEDDING_DIMENSION","768")

CHUNK_SIZE:int =int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP:int = int(os.getenv("CHUNK_OVERLAP", "100"))

FLASK_ENV: str        = os.getenv("FLASK_ENV", "development")
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret")
FLASK_PORT: int       = int(os.getenv("FLASK_PORT", "8080"))
FLASK_DEBUG: bool     = FLASK_ENV == "development"

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR: Path  = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

DATA_DIR: Path = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

RETRIEVER_TOP_K: int     = int(os.getenv("RETRIEVER_TOP_K", "5"))
MAX_TOKENS_RESPONSE: int = int(os.getenv("MAX_TOKENS_RESPONSE", "1024"))
LLM_TEMPERATURE: float   = float(os.getenv("LLM_TEMPERATURE", "0.3"))

SUPABASE_URL: str         = _require("SUPABASE_URL")
SUPABASE_SERVICE_KEY: str = _require("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY: str    = os.getenv("SUPABASE_ANON_KEY", "")
JWT_SECRET: str           = _require("JWT_SECRET")
JWT_EXPIRY_HOURS: int     = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
