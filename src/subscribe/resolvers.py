import json
import uuid
from typing import AsyncIterator

import strawberry
from strawberry import Info
from strawberry.fastapi import GraphQLRouter

from src.database.redis_connector import get_redis
from src.database.redis_train import GROUP_NAME, STREAM_KEY, ensure_group, rd_stm
from src.gql.deps import auth_current_user, _collect_headers
from src.subscribe import BlogSnapshot


@strawberry.type
class Query:
    @strawberry.field
    async def test_temp(self) -> str:
        return 'fuck'


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def test_following(self, info: Info) -> AsyncIterator[BlogSnapshot]:
        # headers = _collect_headers(info)
        # rd = get_redis()
        user = await auth_current_user(_collect_headers(info), get_redis())
        if not user:
            raise Exception("UNAUTHORIZED")

        # 确认存在消费组？
        await ensure_group()

        consumer_name = f"sub-{uuid.uuid4().hex}"
        while True:
            entries = await rd_stm.xreadgroup(
                groupname=GROUP_NAME,
                consumername=consumer_name,
                streams={STREAM_KEY: ">"},
                count=10,
                block=5000,
            )

            if not entries:
                continue

            for _, messages in entries:
                for msg_id, fields in messages:
                    receiver_id = str(fields.get("receiver_id") or "")
                    if receiver_id != str(user):
                        await rd_stm.xack(STREAM_KEY, GROUP_NAME, msg_id)
                        continue

                    data = json.loads(fields.get("data") or "{}")
                    await rd_stm.xack(STREAM_KEY, GROUP_NAME, msg_id)
                    yield BlogSnapshot(**data)


subscribe = strawberry.Schema(subscription=Subscription, query=Query)
subscribeRouter = GraphQLRouter(subscribe, path="/gql/subql")
