import strawberry
from strawberry.fastapi import GraphQLRouter

from src.gql.deps import get_context
from src.user.schemas import UserProfile

from src.user.services import query_user


@strawberry.type
class Query:
    @strawberry.field
    async def get_user_profile(self, info: strawberry.Info) -> UserProfile:
        # 解包所有依赖
        phone, db = info.context["phone"], info.context["db"]

        try:
            return await query_user(phone, db)
        except Exception as e:
            raise strawberry.GraphQLError(str(e))


user_schema = strawberry.Schema(query=Query)
gql_userRouter = GraphQLRouter(user_schema, path="/gql/userql", context_getter=get_context)
