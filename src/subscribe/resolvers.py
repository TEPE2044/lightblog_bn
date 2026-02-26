import asyncio
import json
import uuid
from typing import AsyncIterator

import strawberry
from strawberry import Info
from strawberry.fastapi import GraphQLRouter

from src.database.redis_connector import get_redis
from src.database.redis_train import GROUP_NAME, STREAM_KEY, ensure_group, rd_stm
from src.gql.deps import auth_current_user, _collect_headers
from src.subscribe import EventSnapshot


@strawberry.type
class Query:
    @strawberry.field
    async def test_temp(self) -> str:
        return 'fuck'


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def push_event(self, info: Info) -> AsyncIterator[EventSnapshot]:
        # headers = _collect_headers(info)
        # rd = get_redis()
        # AsyncIterator 意思是 这个函数不是一次返回一个值，而是异步地持续产出多个BlogSnapshot
        phone = await auth_current_user(_collect_headers(info), get_redis())
        if not phone:
            raise Exception("UNAUTHORIZED")

        # 确认存在消息流
        await ensure_group()
        # 为坠落的人类命名（
        consumer_name = f"sub-{uuid.uuid4().hex}"
        # 订阅场景的长循环
        try:
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
                        if receiver_id != str(phone):
                            await rd_stm.xack(STREAM_KEY, GROUP_NAME, msg_id)
                            continue

                        event_type = str(fields.get("event_type") or "blog.published")
                        payload = fields.get("data") or "{}"

                        if not isinstance(payload, str):
                            payload = json.dumps(payload, ensure_ascii=False)

                        await rd_stm.xack(STREAM_KEY, GROUP_NAME, msg_id)
                        yield EventSnapshot(eventType=event_type, payload=payload)
                        # yield：产出一个值并“暂停”，下次还能从暂停点继续执行。
        except asyncio.CancelledError as e:
            raise e


subscribe = strawberry.Schema(subscription=Subscription, query=Query)
subscribeRouter = GraphQLRouter(subscribe, path="/gql/subql")
