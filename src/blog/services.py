from typing import Dict

from sqlalchemy import select, and_, insert
from src.blog.schemas import BlogData
from src.database import db_dependency
from src.orm.model import Blog, blogs_tags, Tag
from sqlalchemy.dialects.postgresql import insert as prt  # 用 pg 的 upsert


# 获取博客
async def get_blogs(rid: int, db: db_dependency) -> Dict | None:
    # 满足条件：是发布的、是正常的、有id的
    try:
        stmt = (select(Blog).where(
            and_(
                Blog.type == 'published',
                Blog.state == 'normal',
                Blog.id == rid
            )
        ))
        # 只可有一条，但是允许是空的
        blog = (await db.execute(stmt)).scalar_one_or_none()
        if not blog:
            return None
        print(blog.title)
        return {
            "title": blog.title,
            "content": blog.content,
            "updated_at": blog.updated_at,
            "type": blog.type
        }
    except Exception as e:
        print(e)
        return None


# 获取博客草稿
async def get_drafts(rid: int, db: db_dependency) -> Dict | None:
    try:
        stmt = (select(Blog).where(
            and_(
                Blog.type == 'draft',
                Blog.state == 'normal',
                Blog.id == rid
            )
        ))
        # 只可有一条，但是允许是空的
        blog = (await db.execute(stmt)).scalar_one_or_none()
        if not blog:
            return None
        print(blog.title)
        return {
            "title": blog.title,
            "content": blog.content,
            "updated_at": blog.updated_at,
            "type": blog.type
        }
    except Exception as e:
        print(e)
        return None



async def upsert_blog(data: BlogData, db: db_dependency) -> bool:
    try:
        async with db.begin():
            # TODO:还是太迟了
            if data.tags:
                filter_tags = set(data.tags)
            # 先插入title和content，并且最终返回插入后的内容blog
            insert_blog = prt(Blog).values(title=data.title, content=data.content).returning(Blog)
            blog = (await db.execute(insert_blog)).scalar_one()
            blog_id = blog.id
            print(blog_id)
            # 如果有tags，插入tags到Tag表中，tags的格式['apple','egg','pen']

            # insert_tag = prt(Tag).values([{"name": tag} for tag in set(data.tags)]).returning(Tag)
            insert_tag = prt(Tag).values([{"name": tag} for tag in filter_tags]).returning(Tag)
            tags = (await db.execute(insert_tag)).all()
            # 提取成一个列表
            tag_ids = [t[0].id for t in tags]

            # blogs_tags 合成大西瓜
            bt_collection = [{"blog_id": blog_id, "tag_id": tid} for tid in tag_ids]

            # 如果有bt_collection，写库
            if bt_collection:
                await db.execute(insert(blogs_tags).values(bt_collection))

        return True
    except Exception as e:
        print(e)
        return False
