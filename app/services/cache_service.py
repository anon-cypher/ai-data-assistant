import redis
import os

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

import json
from decimal import Decimal

CACHE_TTL_SECONDS = 3600


def json_serializer(obj):
    """Convert non-serializable objects (like Decimal)"""
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)


def set_cache(key: str, value):
    redis_client.setex(
        key,
        CACHE_TTL_SECONDS,
        json.dumps(value, default=json_serializer)
    )


def get_cache(key: str):
    data = redis_client.get(key)
    return json.loads(data) if data else None


def clear_cache():
    redis_client.flushdb()
