from sqlalchemy import select
from sqlalchemy.orm import dependency

from src.orm import UserTypeEnum
from src.orm.model import User


async def query_user_basic(phone: str, db: dependency) -> UserTypeEnum | None:
    return await db.scalar(select(User.type, User.username, User.reks_id).where(User.phone == phone))
