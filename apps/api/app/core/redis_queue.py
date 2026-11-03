from __future__ import annotations

from functools import lru_cache

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from rq import Queue

from app.core.config import get_settings

_QUEUE_NAME = "indexbeef"


@lru_cache(maxsize=1)
def _get_redis() -> Redis:
    s = get_settings()
    return Redis(host=s.redis_host, port=s.redis_port, socket_connect_timeout=2)


def get_queue() -> Queue | None:
    """Retorna a fila RQ ou None se Redis nao estiver disponivel."""
    try:
        r = _get_redis()
        r.ping()
        return Queue(_QUEUE_NAME, connection=r)
    except (RedisConnectionError, Exception):
        return None
