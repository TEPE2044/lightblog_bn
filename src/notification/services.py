from sqlalchemy import select
from src.database.pg_connector import SessionLocal
from src.notification.schemas import Notif
from src.orm.model import Blog


async def post_notif(nt: Notif) -> bool:
    print(nt)
    # 这里需要异步上下文管理器
    async with SessionLocal() as db:
        # TODO:改写成插入blog表
        # notice作为一种blog类型 改：notification作为一种博客类型
        return False
        # stmt = select(Blog).where(Blog.id == 14)
        # res = (await db.execute(stmt)).mappings().first()
        # return res
