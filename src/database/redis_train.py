import redis.asyncio as redis
from src.config import settings

# redis = aioredis.from_url(settings.rd_train_url)
# train = redis.pubsub()

rd_stm = redis.from_url(settings.rd_train_url, decode_responses=True)

STREAM_KEY = "ReKindlers"
GROUP_NAME = "REKS_BROADCAST"


async def ensure_group():
    try:
        await rd_stm.xgroup_create(STREAM_KEY, GROUP_NAME, id="0", mkstream=True)
    except Exception:
        print("消费组存在，已建立连接")
        pass