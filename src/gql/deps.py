from typing import Annotated

from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import rd_dependency, get_db
from src.user.services import auth_current_user

"""
GraphQL 专用：把 str | bool 转成 str，失败时抛异常
"""


async def graphql_auth_adapter(request: Request, rd: rd_dependency) -> str:
    result = await auth_current_user(request, rd)
    if result is False:
        raise Exception("Unauthorized")
    return result


async def gql_db(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


gl_auth_phone = Annotated[str, Depends(graphql_auth_adapter)]

"""这就是他们'心意相通'的桥梁"""


async def get_context(
        phone: Annotated[str, Depends(graphql_auth_adapter)],
        db: Annotated[AsyncSession, Depends(gql_db)],
) -> dict:
    return {
        "phone": phone,
        "db": db,
    }
