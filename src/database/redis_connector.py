from functools import lru_cache

import redis.asyncio as redis

# 用异步的redis客户端
# aioredis 已经合并进 redis-py了

from src.config import settings



@lru_cache
def get_redis() -> redis.Redis:
    return redis.from_url(
        settings.rd_local_url,
        encoding='utf-8',
        decode_responses=True
    )


async def get_redis_conn():
    conn = get_redis()
    try:
        yield conn
    finally:
        await conn.close()
