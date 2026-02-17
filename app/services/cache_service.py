import redis
import os
from app.utils.config import RedisConfig

redis_host = os.getenv(RedisConfig.REDIS_URL_ENV, "localhost")
redis_port = int(os.getenv(RedisConfig.REDIS_PORT_ENV, 6379))
redis_db = int(os.getenv(RedisConfig.REDIS_DB_ENV, 0))

redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

import json
from decimal import Decimal

def json_serializer(obj):
    """Convert non-serializable objects (like Decimal) into JSON-friendly types.

    Args:
     - obj: The object to serialize.

    Return:
     - A JSON-serializable representation (e.g., float for Decimal, str otherwise).
    """
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)


def set_cache(key: str, value):
    """Set `value` into Redis at `key` with configured TTL.

    Args:
     - key: Redis key under which to store the value.
     - value: A JSON-serializable Python object to store.

    Return:
     - None
    """
    redis_client.setex(
        key,
        int(os.getenv("CACHE_TTL_SECONDS", RedisConfig.CACHE_TTL_SECONDS)),
        json.dumps(value, default=json_serializer)
    )

def get_cache(key: str):
    """Return the JSON-deserialized value for `key` or `None` if missing.

    Args:
     - key: Redis key to retrieve.

    Return:
     - The deserialized Python object, or `None` if the key does not exist.
    """
    data = redis_client.get(key)
    return json.loads(data) if data else None

def clear_cache():
    """Clear the entire Redis database (use with caution).

    Args:
     - None

    Return:
     - None
    """
    redis_client.flushdb()
