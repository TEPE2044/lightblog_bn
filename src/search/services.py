from typing import Dict

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import aliased

from src.database import db_dependency
from src.database.pg_connector import SessionLocal
from src.orm import BlogStateEnum
from src.orm.model import Blog, User


# ** premature optimization（过早优化）** 是浪费时间。
async def query_blogs_paginated_by_content(
        content: str,  # 模糊查询关键词
        state_: BlogStateEnum,
        page: int,
        page_size: int,
) -> tuple[list[Dict], int]:
    async with SessionLocal() as db:
        # 偏移量（要跳过的条数）
        offset = (page - 1) * page_size
        try:
            # 筛选条件：正常博客、内容关键字模糊查询、标题模糊查询
            filters = [Blog.state == state_,
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

            # 组装结果
            result = [
                {
                    "id": b.id,
                    "cover": b.cover[0] if b.cover else None,
                    "title": b.title,
                    "type": b.type,
                    "created_at": b.created_at,
                    "author": {  # 嵌套作者信息
                        "id": b.reks_id,
                        "name": b.user_name,
                        "avatar": b.user_avatar
                    }
                }
                for b in blogs
            ]

            return result, total

        except Exception as e:
            print(f"分页查询失败: {e}")
            await db.rollback()
            return [], 0
