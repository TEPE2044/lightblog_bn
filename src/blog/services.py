import hashlib
from typing import Dict, Optional

from fastapi import UploadFile
from sqlalchemy import select, insert, func, and_, update
from sqlalchemy.orm import selectinload
from src.blog.schemas import BlogData
from src.database import db_dependency
from src.orm import BlogStateEnum
from src.orm import MusicTypeEnum
from src.orm.model import Blog, blogs_tags, Tag, Gallery, User, BlogLike
from sqlalchemy.dialects.postgresql import insert as prt  # 用 pg 的 upsert


def _normalize_cover_list(raw_cover) -> list[str]:
    """Normalize cover field to stable list[str] for frontend rendering."""
    if isinstance(raw_cover, list):
        return [str(item) for item in raw_cover if item]
    if isinstance(raw_cover, str):
        return [raw_cover] if raw_cover.strip() else []
    return []


# 获取博客
async def get_blog(id: int, _type: str, db: db_dependency,
                   phone: Optional[str] = None) -> Dict | None:
    # Select the ORM Blog entity and eager-load tags to get a proper list[Tag]
    # options(selectinload(Blog.tags)) 会在查询博客时同时查询关联的标签，避免了N+1问题
    if phone:
        # 获取草稿
        stmt = (select(Blog, User.username).options(selectinload(Blog.tags))
                .join(User, Blog.rid == User.reks_id).where(Blog.id == id, Blog.state == _type,
                                                            User.phone == phone))
    else:
        # 获取博客
        stmt = (select(Blog, User.username, User.avatar).options(selectinload(Blog.tags))
                .join(User, Blog.rid == User.reks_id).where(Blog.id == id, Blog.state == _type))

    try:
        result = await db.execute(stmt)
        # 这玩意确实只返回一个，但是它的内容全都在这个对象里！不关scalar或者mappin的事
        row = result.one_or_none()
        if row is None:
            return None
        if phone:
            blog, author = row  # blog 是 ORM Blog 对象，author 是 username 字段
            avatar = None
        else:
            blog, author, avatar = row
        # 结果：<src.orm.model.Blog object at 0x0000028208F4A5F0>
        # blog.tags is a list of Tag objects; return tag names
        tags = [t.name for t in getattr(blog, 'tags', [])]

        return {
            "content": blog.content,
            "title": blog.title,
            "tags": tags,
            "author": author,
            "avatar": avatar,
            "user_id": blog.rid
        }
    except Exception as e:
        print(e)
        return None


async def create_or_update_blog_core(data: BlogData, rid: int, blog_id: int, type_: int,
                                     db: db_dependency, state_: Optional[int] = None) -> int:
    """核心：插入或更新 Blog 行并处理 tags（不提交事务）。
    返回 blog_id，调用者负责提交或回滚事务。
    """
    # is_create 是否新建，判断依据，blog_id是否为0，是->新建，不是->更新
    is_create = (blog_id == 0)

    # 插入或 upsert Blog 表并返回 Blog 行
    if is_create:
        if state_:
            stmt = prt(Blog).values(
                title=data.title,
                content=data.content,
                rid=rid,
                cover=data.cover,
                type=type_,
                state=state_  # 草稿用
            ).returning(Blog)
        else:
            stmt = prt(Blog).values(
                title=data.title,
                content=data.content,
                rid=rid,
                cover=data.cover,
                type=type_
            ).returning(Blog)
    else:
        stmt = (
            update(Blog)
            .where(Blog.id == blog_id, Blog.rid == rid, Blog.state != BlogStateEnum.delete)
            .values(
                title=data.title,
                content=data.content,
                cover=data.cover,
                updated_at=func.now(),
            )
            .returning(Blog)
        )

    blog = (await db.execute(stmt)).scalar_one_or_none()
    if blog is None:
        raise ValueError("blog not found or not owned by current user")
    blog_id = blog.id

    # 删除旧的标签关联
    await db.execute(
        blogs_tags.delete().where(blogs_tags.c.blog_id == blog_id)
    )

    # 处理 tags：strip / 过滤 None / 去重并保序 / 最多 5 个
    raw_tags = data.tags or []
    tags = list(dict.fromkeys(
        (str(raw).strip() for raw in raw_tags if raw is not None and str(raw).strip() != "")
    ))[:5]

    if tags:
        insert_tag = prt(Tag).values([{"name": tag} for tag in tags]
                                     ).on_conflict_do_update(index_elements=["name"],
                                                             set_={"updated_at": func.now()}
                                                             ).returning(Tag)
        tag_rows = (await db.execute(insert_tag)).all()
        tag_ids = [row[0].id for row in tag_rows]
        bt_collection = [{"blog_id": blog_id, "tag_id": tid} for tid in tag_ids]
        if bt_collection:
            await db.execute(insert(blogs_tags).values(bt_collection))

    return blog_id


async def upsert_blog(data: BlogData, rid: int, blog_id: int, type_: int,
                      db: db_dependency, state_: Optional[int] = None) -> bool:
    """事务包装：调用 core 执行并负责 commit/rollback"""
    try:
        _ = await create_or_update_blog_core(data, rid, blog_id, type_, db, state_)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        print(e)
        return False


# 无分页
async def query_user_blogs(rid: int, state_: BlogStateEnum, db: db_dependency) -> list[Dict] | None:
    try:
        join_blog = select(Blog.id, Blog.cover, Blog.title, Blog.type, Blog.created_at).where(
            and_(Blog.rid == rid, Blog.state == state_)).order_by(Blog.updated_at.desc())
        blogs = (await db.execute(join_blog)).mappings().all()
        blog_ids = [int(blog.id) for blog in blogs]
        result = [
            {
                "id": blog.id,
                "cover": _normalize_cover_list(blog.cover),
                "title": blog.title,
                "type": int(blog.type),
                "created_at": blog.created_at,
                "author": blog.username,
                "avatar": blog.avatar
            }
            for blog in blogs
        ]
        # print(result)
        return result
    except Exception as e:
        print(e)
        return None


async def query_user_blogs_cursor(
        rid: int,
        state_: BlogStateEnum,
        cursor: int | None,
        limit: int,
        db: db_dependency,
) -> Dict | None:
    try:
        stmt = select(Blog.id, Blog.cover, Blog.title, Blog.type, Blog.created_at).where(Blog.rid == rid,
                                                                                         Blog.state == state_)
        if cursor is not None:
            stmt = stmt.where(Blog.id < cursor)

        rows = (
            await db.execute(stmt.order_by(Blog.id.desc()).limit(limit + 1))
        ).mappings().all()

        has_more = len(rows) > limit
        page_rows = rows[:limit]
        page_blog_ids = [int(row.id) for row in page_rows]
        items = [
            {
                "id": row.id,
                "cover": _normalize_cover_list(row.cover),
                "title": row.title,
                "type": int(row.type),
                "created_at": row.created_at,
            }
            for row in page_rows
        ]

        next_cursor = items[-1]["id"] if has_more and len(items) > 0 else None
        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    except Exception as e:
        print(e)
        return None


# 每日推荐
async def query_daily_blog(db: db_dependency) -> list[Dict] | None:
    try:
        stmt = (select(Blog.id, Blog.cover, Blog.title, Blog.type, Blog.created_at, User.username)
                .join(User, Blog.rid == User.reks_id).order_by(func.random()).limit(10))
        blogs = (await db.execute(stmt)).all()
        return [
            {
                "id": id_,  # ← 直接是变量名，清晰
                "cover": cover,
                "title": title,
                "type": type_,
                "created_at": created_at,
                "author": username
            }
            for id_, cover, title, type_, created_at, username in blogs  # ← 元组解包
        ]
    except Exception as e:
        print(e)
        return None


async def query_hot_blog_by_likes(limit: int, db: db_dependency) -> list[Dict] | None:
    try:
        like_subq = (
            select(
                BlogLike.blog_id.label("blog_id"),
                func.count(BlogLike.id).label("like_count"),
            )
            .group_by(BlogLike.blog_id)
            .subquery()
        )

        stmt = (
            select(
                Blog.id,
                Blog.cover,
                Blog.title,
                Blog.type,
                Blog.created_at,
                User.username,
                User.avatar,
                User.reks_id,
                func.coalesce(like_subq.c.like_count, 0).label("like_count"),
            ).join(User, User.reks_id == Blog.rid)
            .outerjoin(like_subq, like_subq.c.blog_id == Blog.id)
            .where(Blog.state == BlogStateEnum.publish)
            .order_by(func.coalesce(like_subq.c.like_count, 0).desc(), Blog.created_at.desc())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).mappings().all()
        blog_ids = [int(row.id) for row in rows]
        return [
            {
                "id": row.id,
                "cover": _normalize_cover_list(row.cover),
                "title": row.title,
                "type": int(row.type),
                "created_at": row.created_at,
                "like_count": int(row.like_count or 0),
                "author": row.username,
                "avatar": row.avatar,
                "user_id": row.reks_id
            }
            for row in rows
        ]
    except Exception as e:
        print(e)
        return None


async def query_hot_blog_cursor(
        cursor: int | None,
        limit: int,
        db: db_dependency,
) -> Dict | None:
    try:
        like_subq = (
            select(
                BlogLike.blog_id.label("blog_id"),
                func.count(BlogLike.id).label("like_count"),
            )
            .group_by(BlogLike.blog_id)
            .subquery()
        )

        stmt = (
            select(
                Blog.id,
                Blog.cover,
                Blog.title,
                Blog.type,
                Blog.created_at,
                func.coalesce(like_subq.c.like_count, 0).label("like_count"),
                User.username,
                User.avatar,
                User.reks_id
            ).join(User, User.reks_id == Blog.rid)
            .outerjoin(like_subq, like_subq.c.blog_id == Blog.id)
            .where(Blog.state == BlogStateEnum.publish)
        )

        if cursor is not None:
            stmt = stmt.where(Blog.id < cursor)

        rows = (
            await db.execute(
                stmt.order_by(
                    func.coalesce(like_subq.c.like_count, 0).desc(),
                    Blog.id.desc(),
                ).limit(limit + 1)
            )
        ).mappings().all()

        has_more = len(rows) > limit
        page_rows = rows[:limit]
        blog_ids = [int(row.id) for row in page_rows]

        items = [
            {
                "id": row.id,
                "cover": _normalize_cover_list(row.cover),
                "title": row.title,
                "author": row.author,
                "type": int(row.type),
                "created_at": row.created_at,
                "like_count": int(row.like_count or 0),
                "avatar": row.avatar,
                "user_id": row.reks_id
            }
            for row in page_rows
        ]

        next_cursor = items[-1]["id"] if has_more and len(items) > 0 else None
        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    except Exception as e:
        print(e)
        return None


async def insert_into_gallery(rid: int, href: str, md5: str, db: db_dependency) -> bool:
    stmt = insert(Gallery).values(rid=rid, url=href, alt=f"reks-{href}", md5=md5).returning(
        Gallery.id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    await db.commit()
    # print(row)
    if row is not None:
        return True
    else:
        return False


# 计算MD5 看不懂但是很牛逼
async def file_md5(upload_file: UploadFile) -> str:
    hasher = hashlib.md5()
    while chunk := await upload_file.read(8192):
        hasher.update(chunk)
    await upload_file.seek(0)
    return hasher.hexdigest()


# 查找重复项
async def query_by_hash(md5: str, db: db_dependency) -> str | None:
    stmt = select(Gallery.url).filter(Gallery.md5 == md5).limit(1)
    return (await db.execute(stmt)).scalar_one_or_none()


# 软删除博客
async def soft_delete_blog(db: db_dependency, blog_id: int, rid: int) -> bool:
    stmt = update(Blog).where(Blog.id == blog_id, Blog.rid == rid).values(state="delete")
    try:
        res = await db.execute(stmt)
        await db.commit()
        if res.rowcount > 0:
            return True
        return False
    except Exception as e:
        await db.rollback()
        print(e)
        return False


async def _publish_draft(blog_id: int, rid: int, db: db_dependency) -> bool:
    stmt = update(Blog).values(state='publish').where(Blog.id == blog_id, Blog.rid == rid)
    try:
        res = await db.execute(stmt)
        await db.commit()
        if res.rowcount > 0:
            return True
        return False
    except Exception as e:
        await db.rollback()
        print(e)
        return False
