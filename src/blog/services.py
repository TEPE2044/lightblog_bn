from sqlalchemy import select

from src.database import db_dependency
from src.orm.model import Blog


# 获取博客
async def get_blogs(rid: int, db: db_dependency):
    stmt = (select(Blog.title, Blog.content, Blog.updated_at, Blog.tags)
            .where(Blog.type == 1 and Blog.state == 'normal' and Blog.id == rid))
    res = await db.execute(stmt)
    return res.all()


# 获取博客草稿
async def get_drafts(rid: int, db: db_dependency):
    stmt = (select(Blog.title, Blog.content, Blog.updated_at, Blog.tags)
            .where(Blog.type == 0 and Blog.state == 'normal' and Blog.id == rid))
    res = await db.execute(stmt)
    return res.all()

async def upload_blog():
    pass
