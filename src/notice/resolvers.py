import strawberry
from fastapi import HTTPException
from strawberry import Info
from strawberry.fastapi import GraphQLRouter

from src.database.redis_connector import get_redis
from src.gql import HTTPResult
from src.gql.deps import auth_current_user, _collect_headers
from src.notice.schemas import Notice
from src.notice.services import post_notice


@strawberry.type
class Query:
    @strawberry.field
    async def getNotice(self) -> str:
        return "pass"


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def addNotice(self, info: Info, nt: Notice) -> HTTPResult:
        phone = await auth_current_user(_collect_headers(info), get_redis())

        if not phone:
            raise HTTPException(status_code=401)
        res = await post_notice(nt)
        if res is True:
            return HTTPResult(status=200, msg="公告发布成功")
        else:
            raise HTTPException(status_code=404)


notice = strawberry.Schema(query=Query, mutation=Mutation)
noticeRouter = GraphQLRouter(notice, path='/gql/notice')
