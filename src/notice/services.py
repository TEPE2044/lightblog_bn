from sqlalchemy import select
from src.database.pg_connector import SessionLocal
from src.notice.schemas import Notice
from src.orm.model import Blog


async def post_notice(notice: Notice) -> bool:
    print(notice)
    # 这里需要异步上下文管理器
    async with SessionLocal() as db:
        # TODO:改写成插入blog表
        # notice作为一种blog类型
        return False
        # stmt = select(Blog).where(Blog.id == 14)
        # res = (await db.execute(stmt)).mappings().first()
        # return res
