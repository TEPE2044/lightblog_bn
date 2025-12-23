from typing import Dict

import strawberry
from src.user.gql.query import UserQuery


@strawberry.type
class RootQuery(UserQuery):
    @strawberry.field(description="草莓根目录")
    async def hello(self) -> str:
        return "ReKindlers-草莓味音乐轻博客平台"

    @strawberry.field(description="测试查询")
    async def query_something(self) -> int:
        return 2

    @strawberry.field(description="测试查询数字")
    async def query_number(self) -> int:
        return 42


schema = strawberry.Schema(query=RootQuery)
