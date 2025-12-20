import strawberry
from .resolver import resolve_me
from .types import UserGQL


@strawberry.type
class UserQuery:
    @strawberry.field(description="当前登录用户基本信息")
    async def me(self, info) -> UserGQL:
        return await resolve_me(info)

