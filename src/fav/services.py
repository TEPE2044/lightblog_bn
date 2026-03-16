from sqlalchemy import delete, func, insert, select

from src.blog.services import _query_music_meta_by_blog_ids
from src.database import db_dependency
from src.fav.schemas import FavoriteTargetEnum
from src.orm import BlogStateEnum
from src.orm.model import Blog, BlogFavorite, BlogLike, Music, MusicFavorite, User


async def _ensure_blog_exists(blog_id: int, db: db_dependency) -> bool:
    stmt = select(Blog.id).where(
        Blog.id == blog_id,
        Blog.state == BlogStateEnum.publish,
    )
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def _ensure_music_exists(music_id: int, db: db_dependency) -> bool:
    stmt = select(Music.id).where(
        Music.id == music_id,
        Music.state == BlogStateEnum.publish,
    )
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def query_favorite_status(target_id: int, target_type: FavoriteTargetEnum,
                                rid: int, db: db_dependency) -> bool:
    if target_type == FavoriteTargetEnum.blog:
        stmt = select(BlogFavorite.id).where(
            BlogFavorite.user_id == rid,
            BlogFavorite.blog_id == target_id,
        )
    else:
        stmt = select(MusicFavorite.id).where(
            MusicFavorite.user_id == rid,
            MusicFavorite.music_id == target_id,
        )
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def query_like_status(blog_id: int, rid: int, db: db_dependency) -> bool:
    stmt = select(BlogLike.id).where(
        BlogLike.user_id == rid,
        BlogLike.blog_id == blog_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def query_like_count(blog_id: int, db: db_dependency) -> int | None:
    if not await _ensure_blog_exists(blog_id, db):
        return None

    stmt = select(func.count(BlogLike.id)).where(BlogLike.blog_id == blog_id)
    count = (await db.execute(stmt)).scalar_one()
    return int(count or 0)


async def query_like_status_map(blog_ids: list[int], rid: int,
                                db: db_dependency) -> dict[int, bool]:
    if len(blog_ids) == 0:
        return {}

    stmt = select(BlogLike.blog_id).where(
        BlogLike.user_id == rid,
        BlogLike.blog_id.in_(blog_ids),
    )
    rows = (await db.execute(stmt)).scalars().all()
    existed_ids = {int(item) for item in rows}
    return {int(blog_id): int(blog_id) in existed_ids for blog_id in blog_ids}


async def query_favorite_status_map(target_ids: list[int], target_type: FavoriteTargetEnum,
                                    rid: int, db: db_dependency) -> dict[int, bool]:
    if len(target_ids) == 0:
        return {}

    if target_type == FavoriteTargetEnum.blog:
        stmt = select(BlogFavorite.blog_id).where(
            BlogFavorite.user_id == rid,
            BlogFavorite.blog_id.in_(target_ids),
        )
    else:
        stmt = select(MusicFavorite.music_id).where(
            MusicFavorite.user_id == rid,
            MusicFavorite.music_id.in_(target_ids),
        )

    rows = (await db.execute(stmt)).scalars().all()
    existed_ids = {int(item) for item in rows}
    #  return {int(target_id): (int(target_id) in existed_ids) for target_id in target_ids}
    return {int(target_id): int(target_id) in existed_ids for target_id in target_ids}

# 收藏
async def set_favorite(target_id: int, target_type: FavoriteTargetEnum,
                       rid: int, favorited: bool, db: db_dependency) -> dict | None:
    try:
        # 如果目标类型是blog
        if target_type == FavoriteTargetEnum.blog:
            # 未发布的博客和不存在的博客，直接return None
            if not await _ensure_blog_exists(target_id, db):
                return None
            # 在表中找对应的选项
            existed_stmt = select(BlogFavorite.id).where(
                BlogFavorite.user_id == rid,
                BlogFavorite.blog_id == target_id,
            )
            existed = (await db.execute(existed_stmt)).scalar_one_or_none()
            # 如果前端状态是true，证明新点赞的
            if favorited:
                # 没有这条点赞记录，插入新记录
                if existed is None:
                    await db.execute(insert(BlogFavorite).values(user_id=rid, blog_id=target_id))
                await db.commit()
                return {"msg": "收藏成功", "is_favorited": True}
            # 已经点过赞了，删掉
            if existed is not None:
                await db.execute(delete(BlogFavorite).where(BlogFavorite.id == existed))
            await db.commit()
            return {"msg": "取消收藏成功", "is_favorited": False}

        # 同理可得，目标类型是music
        if not await _ensure_music_exists(target_id, db):
            return None

        existed_stmt = select(MusicFavorite.id).where(
            MusicFavorite.user_id == rid,
            MusicFavorite.music_id == target_id,
        )
        existed = (await db.execute(existed_stmt)).scalar_one_or_none()
        if favorited:
            if existed is None:
                await db.execute(insert(MusicFavorite).values(user_id=rid, music_id=target_id))
            await db.commit()
            return {"msg": "收藏成功", "is_favorited": True}

        if existed is not None:
            await db.execute(delete(MusicFavorite).where(MusicFavorite.id == existed))
        await db.commit()
        return {"msg": "取消收藏成功", "is_favorited": False}
    except Exception as e:
        print(e)
        await db.rollback()
        return False


# 点赞
async def set_like(blog_id: int, rid: int, liked: bool, db: db_dependency) -> dict | None:
    try:
        if not await _ensure_blog_exists(blog_id, db):
            return None

        existed_stmt = select(BlogLike.id).where(
            BlogLike.user_id == rid,
            BlogLike.blog_id == blog_id,
        )
        existed = (await db.execute(existed_stmt)).scalar_one_or_none()

        if liked:
            if existed is None:
                await db.execute(insert(BlogLike).values(user_id=rid, blog_id=blog_id))
            await db.commit()
            like_count = await query_like_count(blog_id, db)
            return {"msg": "点赞成功", "is_liked": True, "like_count": int(like_count or 0)}

        if existed is not None:
            await db.execute(delete(BlogLike).where(BlogLike.id == existed))
        await db.commit()
        like_count = await query_like_count(blog_id, db)
        return {"msg": "取消点赞成功", "is_liked": False, "like_count": int(like_count or 0)}
    except Exception as e:
        print(e)
        await db.rollback()
        return False


async def _query_blog_favorites(rid: int, db: db_dependency) -> list[dict]:
    stmt = (
        select(
            BlogFavorite.created_at.label("favorited_at"),
            Blog.id,
            Blog.cover,
            Blog.title,
            Blog.type,
            Blog.created_at,
            User.reks_id.label("author_rid"),
            User.username,
            User.avatar,
        )
        .join(Blog, BlogFavorite.blog_id == Blog.id)
        .join(User, Blog.rid == User.reks_id)
        .where(
            BlogFavorite.user_id == rid,
            Blog.state == BlogStateEnum.publish,
        )
        .order_by(BlogFavorite.created_at.desc())
    )
    rows = (await db.execute(stmt)).mappings().all()
    blog_ids = [int(row.id) for row in rows]
    music_map = await _query_music_meta_by_blog_ids(blog_ids, db)
    return [
        {
            "target_type": FavoriteTargetEnum.blog,
            "favorited_at": row.favorited_at,
            "id": row.id,
            "cover": row.cover,
            "title": row.title,
            "type": row.type,
            "created_at": row.created_at,
            "author_rid": row.author_rid,
            "username": row.username,
            "avatar": row.avatar,
            "music": music_map.get(int(row.id)),
        }
        for row in rows
    ]


async def _query_music_favorites(rid: int, db: db_dependency) -> list[dict]:
    stmt = (
        select(
            MusicFavorite.created_at.label("favorited_at"),
            Music.id,
            Music.name,
            Music.cover,
            Music.audio,
            Music.desc,
            Music.created_at,
            User.reks_id.label("author_rid"),
            User.username,
            User.avatar,
        )
        .join(Music, MusicFavorite.music_id == Music.id)
        .join(User, Music.rid == User.reks_id)
        .where(
            MusicFavorite.user_id == rid,
            Music.state == BlogStateEnum.publish,
        )
        .order_by(MusicFavorite.created_at.desc())
    )
    rows = (await db.execute(stmt)).mappings().all()
    return [
        {
            "target_type": FavoriteTargetEnum.music,
            "favorited_at": row.favorited_at,
            "id": row.id,
            "name": row.name,
            "cover": row.cover,
            "audio": row.audio,
            "desc": row.desc,
            "created_at": row.created_at,
            "author_rid": row.author_rid,
            "username": row.username,
            "avatar": row.avatar,
        }
        for row in rows
    ]


async def query_user_favorites(rid: int, target_type: FavoriteTargetEnum | None,
                               db: db_dependency) -> list[dict]:
    if target_type == FavoriteTargetEnum.blog:
        return await _query_blog_favorites(rid, db)
    if target_type == FavoriteTargetEnum.music:
        return await _query_music_favorites(rid, db)

    rows = await _query_blog_favorites(rid, db)
    rows.extend(await _query_music_favorites(rid, db))
    rows.sort(key=lambda item: item["favorited_at"], reverse=True)
    return rows
