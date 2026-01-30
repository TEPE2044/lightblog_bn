import aioredis

from src.config import settings

redis = aioredis.from_url(settings.rd_train_url)
train = redis.pubsub()


async def deliver_to_fan():
    pass
