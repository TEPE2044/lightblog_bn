from typing import Type

import strawberry
from strawberry.fastapi import GraphQLRouter

from src.search.schemas import Blog
'''
TODO:
1.博客搜索
- 标签搜索 + 模糊搜索 
2.电台搜索 
- 标签搜索 + 模糊搜索 
3.用户搜索
- 模糊搜索 
'''


@strawberry.type
class Query:
    @strawberry.field
    async def blog(self) -> Type[Blog]:
        return Blog

    @strawberry.field
    async def radio(self) -> str:
        pass

    @strawberry.field
    async def user(self) -> str:
        pass


search = strawberry.Schema(query=Query)
searchRouter = GraphQLRouter(search, path="gql/subql")
