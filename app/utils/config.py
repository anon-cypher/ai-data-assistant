import os


class LLMConfig:
    # env var name that holds API key
    OPENAI_API_KEY_ENV = os.getenv("OPENAI_API_KEY", "OPENAI_API_KEY")

    # base url for OpenAI-compatible endpoints
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

    # model mappings
    # model mappings
    MODELS = {
        "small": os.getenv("OPENAI_MODEL_SMALL", "openai/gpt-4o-mini"),
        "embed": os.getenv("OPENAI_EMBEDDING_MODEL", "openai/text-embedding-3-small"),
    }

    # generation defaults
    TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))
    MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "300"))
    # embedding model env name
    EMBEDDING_MODEL_ENV = os.getenv("OPENAI_EMBEDDING_MODEL_ENV", "OPENAI_EMBEDDING_MODEL")


class DBConfig:
    # env var name that holds the database URL
    DATABASE_URL_ENV = os.getenv("DATABASE_URL", "")
    # default schema metadata path (can be overridden via env)
    SCHEMA_METADATA_PATH = os.getenv("SCHEMA_METADATA_PATH", "app/db/schema_metadata.json")

class RedisConfig:
    REDIS_URL_ENV = os.getenv("REDIS_URL_ENV", "REDIS_URL")
    REDIS_PORT_ENV = os.getenv("REDIS_PORT_ENV", "REDIS_PORT")
    REDIS_DB_ENV = os.getenv("REDIS_DB_ENV", "REDIS_DB")
    CACHE_TTL_SECONDS = int(os.getenv("REDIS_CACHE_TTL_SECONDS", "3600"))

# Paths for vector store and metadata
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "app/vector_store")
INDEX_PATH = os.getenv("FAISS_INDEX_PATH", f"{VECTOR_STORE_DIR}/faiss.index")
TABLE_METADATA_PATH = os.getenv("TABLE_METADATA_PATH", f"{VECTOR_STORE_DIR}/table_metadata.json")

class SQLValidatorConfig:
    FORBIDDEN_KEYWORDS = [
        "drop", "delete", "update", "insert", "alter", "truncate", "create"
    ]

    MAX_LIMIT = 1000


# Feature flags
DEEP_AGENT_ENABLED = os.getenv("DEEP_AGENT_ENABLED", "false").lower() in ("1", "true", "yes")

# Logging configuration
# `LOG_ROTATION_WHEN` uses TimedRotatingFileHandler semantics: S, M, H, D, W0-W6.
# For a monthly-like rotation use `D` with `LOG_ROTATION_INTERVAL=30` (default).
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_FILE = os.getenv("LOG_FILE", "assistant.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_ROTATION_WHEN = os.getenv("LOG_ROTATION_WHEN", "D")
LOG_ROTATION_INTERVAL = int(os.getenv("LOG_ROTATION_INTERVAL", "30"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "12"))
