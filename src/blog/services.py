import datetime

from sqlalchemy import select
# 没有真正的upsert
from sqlalchemy.dialects.postgresql import insert
from src.blog.schemas import BlogData
from src.database import db_dependency
from src.orm.model import Blog, blogs_tags, Tag


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


async def upsert_blog(data: BlogData, db: db_dependency):
    try:
        # 多对多表，先插入title和content，tags按需插入
        stmt = (insert(Blog)
                .values(title=data.title, content=data.content).returning(Blog.id))
        res = await db.execute(stmt)
        # await db.commit() fix:先不要提交
        blog_id = res.scalar_one()

        if data.tags:
            # 先插入Tag表
            await db.execute(
                insert(Tag).values([{"name": t} for t in data.tags])
                .on_conflict_do_nothing(index_elements=["name"])
            )
            # 2-b 查出id
            tag_rows = await db.execute(select(Tag.id).where(Tag.name.in_(data.tags)))
            tag_ids = [r[0] for r in tag_rows]

            # 后插入中间表
            await db.execute(
                insert(blogs_tags),
                [{"blog_id": blog_id, "tag_id": tid} for tid in tag_ids]
            )
        await db.commit()
        return blog_id
    except Exception as e:
        print(e)
