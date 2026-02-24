import json
import uuid
from typing import AsyncIterator

import strawberry
from strawberry import Info
from strawberry.fastapi import GraphQLRouter

from src.database.redis_connector import get_redis
from src.database.redis_train import GROUP_NAME, STREAM_KEY, ensure_group, rd_stm
from src.subscribe import BlogSnapshot
from src.user.services import auth_current_user_from_headers


def _collect_headers(info: Info) -> dict[str, str]:
    headers: dict[str, str] = {}
    context = info.context if isinstance(info.context, dict) else {}

    request = context.get("request")
    if request is not None and hasattr(request, "headers"):
        headers.update({str(k): str(v) for k, v in request.headers.items()})

    websocket = context.get("ws") or context.get("websocket")
    if websocket is not None and hasattr(websocket, "headers"):
        headers.update({str(k): str(v) for k, v in websocket.headers.items()})

    params = context.get("connection_params")
    if isinstance(params, dict):
        headers.update({str(k): str(v) for k, v in params.items()})

    return headers


@strawberry.type
class Query:
    @strawberry.field
    async def test_temp(self) -> str:
        return 'fuck'


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def test_following(self, info: Info) -> AsyncIterator[BlogSnapshot]:
        headers = _collect_headers(info)
        rd = get_redis()
        me = await auth_current_user_from_headers(headers, rd)
        if not me:
            raise Exception("UNAUTHORIZED")

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
                    if receiver_id != str(me):
                        await rd_stm.xack(STREAM_KEY, GROUP_NAME, msg_id)
                        continue

                    data = json.loads(fields.get("data") or "{}")
                    await rd_stm.xack(STREAM_KEY, GROUP_NAME, msg_id)
                    yield BlogSnapshot(**data)


sub_schema = strawberry.Schema(subscription=Subscription, query=Query)
subscribeRouter = GraphQLRouter(sub_schema, path="/gql/subql")
