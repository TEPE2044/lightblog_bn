from typing import Dict, List

from sqlalchemy import select, func, and_, or_
from src.database.pg_connector import SessionLocal
from src.orm.model import Blog, User, blogs_tags, Tag


# ** premature optimization（过早优化）** 是浪费时间。
async def query_blogs_paginated_by_content(
        content: str,  # 模糊查询关键词
        page: int,
        page_size: int,
) -> tuple[list[Dict], int]:
    async with SessionLocal() as db:
        # 偏移量（要跳过的条数）
        offset = (page - 1) * page_size
        try:
            # 筛选条件：正常博客、内容关键字模糊查询、标题模糊查询
            filters = [Blog.state == 'publish',
                       or_(
                           Blog.title.ilike(f"%{content}%"),
                           Blog.content.ilike(f"%{content}%")
                       )]

            # 共检索到n条
            count_stmt = (
                select(func.count())
                .select_from(Blog)
                .join(User, Blog.rid == User.reks_id)  # 加上 JOIN 保持一致
                .where(and_(*filters))
            )
            total = (await db.execute(count_stmt)).scalar() or 0

            # 真实数据返回
            data_stmt = (
                select(
                    Blog.id,
                    Blog.cover,
                    Blog.title,
                    Blog.type,
                    Blog.created_at,
                    User.reks_id,
                    User.username.label("user_name"),
                    User.avatar.label("user_avatar")
                )
                .join(User, Blog.rid == User.reks_id)
                .where(and_(*filters))
                .order_by(Blog.updated_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            blogs = (await db.execute(data_stmt)).mappings().all()
            # print(blogs)
            # 组装结果
            result = [
                {
                    "id": b.id,
                    "cover": b.cover[0] if b.cover else None,
                    "title": b.title,
                    "type": b.type,
                    "created_at": b.created_at.isoformat(),
                    "author": {  # 嵌套作者信息
                        "id": b.reks_id,
                        "username": b.user_name,
                        "avatar": b.user_avatar
                    }
                }
                for b in blogs
            ]
            # print(f"service{result}-{total}")
            return result, total

        except Exception as e:
            print(f"分页查询失败: {e}")
            await db.rollback()
            return [], 0


async def query_blogs_paginated_by_tags(
        tags: List[str],
        page: int,
        page_size: int,
) -> tuple[list[Dict], int]:
    async with SessionLocal() as db:
        offset = (page - 1) * page_size

        try:
            # 先把tag_id查出来:子查询、标签过滤、去重
            tagged_blog_ids = (
                select(Blog.id)
                .join(blogs_tags, Blog.id == blogs_tags.c.blog_id)
                .join(Tag, Tag.id == blogs_tags.c.tag_id)
                .where(Tag.name.in_(tags))
                .distinct()
                .subquery()
            )

            # 计数
            count_stmt = select(func.count()).select_from(tagged_blog_ids)

            total = (await db.execute(count_stmt)).scalar() or 0

            # 查详情（不 JOIN Tag，避免 JSON 问题）
            data_stmt = (
                select(
                    Blog.id,
                    Blog.cover,
                    Blog.title,
                    Blog.type,
                    Blog.created_at,
                    User.reks_id,
                    User.username.label("user_name"),
                    User.avatar.label("user_avatar")
                )
                .join(tagged_blog_ids, Blog.id == tagged_blog_ids.c.id)
                .join(User, Blog.rid == User.reks_id)
                .order_by(Blog.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )

            blogs = (await db.execute(data_stmt)).mappings().all()

            result = [
                {
                    **dict(b),
                    "cover": b.cover[0] if b.cover else None,
                    "created_at": b.created_at.isoformat(),
                    "author": {
                        "id": b.reks_id,
                        "username": b.user_name,
                        "avatar": b.user_avatar
                    }
                }
                for b in blogs
            ]

            return result, total

        except Exception as e:
            print(e)
            await db.rollback()
            return [], 0


async def query_user_paginated(who: str, page: int, page_size: int) -> tuple[list[Dict], int]:
    async with (SessionLocal() as db):
        offset = (page - 1) * page_size

        try:
            count_stmt = select(func.count()).where(User.username.ilike(f"%{who}%"))
            total = (await db.execute(count_stmt)).scalar() or 0

            data_stmt = select(User.username, User.avatar, User.signature, User.gender).where(
                User.username.ilike(f"%{who}%")).offset(offset).order_by(User.username).limit(page_size)
            users = (await db.execute(data_stmt)).mappings().all()
            result = [{**dict(user)}for user in users]
            return result, total
        except Exception as e:
            await db.rollback()
            print(e)
            return [], 0
