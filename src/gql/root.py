import strawberry
from src.user.gql.query import UserQuery


@strawberry.type
class RootQuery(UserQuery):
    @strawberry.field(description="草莓根目录")
    async def hello(self) -> str:
        return "ReKindlers-草莓味音乐轻博客平台"


schema = strawberry.Schema(query=RootQuery)
