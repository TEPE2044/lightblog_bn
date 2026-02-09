import strawberry
from strawberry.fastapi import GraphQLRouter

from src.search.schemas import BlogResult

# Info是啥
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
    async def blog_search(self) -> BlogResult:
        # TODO:搜索
        pass
        return BlogResult

    @strawberry.field
    async def radio_search(self) -> str:
        pass

    @strawberry.field
    async def user_search(self) -> str:
        pass


search_schema = strawberry.Schema(query=Query)
searchRouter = GraphQLRouter(search_schema, path="gql/subql")
