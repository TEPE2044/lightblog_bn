import json
from typing import AsyncIterator

import strawberry
from strawberry import Info
from strawberry.fastapi import GraphQLRouter

from src.database.redis_train import train
from src.subscribe import BlogSnapshot


@strawberry.type
class Query:
    @strawberry.field
    def test_temp(self) -> str:
        return 'fuck'


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def test_following(self, info: Info) -> AsyncIterator[BlogSnapshot]:
        me = 1
        await train.subscribe(f"FEED:{me}")
        try:
            async for msg in train.listen():  # ③ 现在可以 async for 了
                if msg['type'] != 'message':
                    continue
                data = json.loads(msg['data'])
                yield BlogSnapshot(**data)
        finally:
            await train.unsubscribe()
            await train.close()


sub_schema = strawberry.Schema(subscription=Subscription, query=Query)
subscribeRouter = GraphQLRouter(sub_schema, path="/gql/subql")
