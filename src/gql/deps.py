from typing import Annotated

from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import rd_dependency, get_db
from src.user.services import auth_current_user


async def gql_db(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


async def get_context(
        db: Annotated[AsyncSession, Depends(gql_db)],
) -> dict:
    return {
        "db": db,
    }
