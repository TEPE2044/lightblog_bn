from typing import AsyncIterator

import strawberry
from strawberry.fastapi import GraphQLRouter



@strawberry.type
class Query:
    @strawberry.field
    async def get_activity(self) -> str:
        pass


notice = strawberry.Schema(query=Query)
noticeRouter = GraphQLRouter(notice, path='gql/notice')
