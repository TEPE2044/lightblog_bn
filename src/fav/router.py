from fastapi import APIRouter, HTTPException

from src.database import db_dependency
from src.fav.schemas import (
    FavoriteBatchStatusBody,
    FavoriteTargetEnum,
    FavoriteToggleBody,
    LikeBatchStatusBody,
    LikeToggleBody,
)
from src.fav.services import (
    query_favorite_status,
    query_favorite_status_map,
    query_like_count,
    query_like_status,
    query_like_status_map,
    query_user_favorites,
    set_favorite,
    set_like,
)
from src.user.services import auth_phone, query_user_rid

favRouter = APIRouter(prefix="/fav", tags=['收藏模块'])


@favRouter.post("/{id}", summary="设置收藏状态")
async def favIt(id: int, body: FavoriteToggleBody, phone: auth_phone, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")

    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")

    result = await set_favorite(id, body.target_type, rid, body.favorited, db)
    if result is None:
        raise HTTPException(404, "目标不存在或不可收藏")
    if result is False:
        raise HTTPException(500, "收藏操作失败")
    return result


@favRouter.get("/status/{id}", summary="获取当前用户收藏状态")
async def fav_status(id: int, target_type: FavoriteTargetEnum, phone: auth_phone,
                     db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")

    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")

    return {
        "msg": "获取成功",
        "is_favorited": await query_favorite_status(id, target_type, rid, db),
    }


@favRouter.post("/status/batch", summary="批量获取当前用户收藏状态")
async def fav_status_batch(body: FavoriteBatchStatusBody, phone: auth_phone, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")

    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")

    return {
        "msg": "获取成功",
        "items": await query_favorite_status_map(body.ids, body.target_type, rid, db),
    }


@favRouter.get("/user/{id}", summary="获取用户收藏的内容")
async def user_fav(id: int, db: db_dependency, target_type: FavoriteTargetEnum | None = None):
    rows = await query_user_favorites(id, target_type, db)
    return {"msg": "获取成功", "favorites": rows}


@favRouter.get("/my-fav", summary="我的收藏")
async def my_fav(phone: auth_phone, db: db_dependency, target_type: FavoriteTargetEnum | None = None):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")

    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")

    rows = await query_user_favorites(rid, target_type, db)
    return {"msg": "获取成功", "favorites": rows}


@favRouter.post("/like/{id}", summary="设置点赞状态")
async def likeIt(id: int, body: LikeToggleBody, phone: auth_phone, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")

    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")

    result = await set_like(id, rid, body.liked, db)
    if result is None:
        raise HTTPException(404, "目标不存在或不可点赞")
    if result is False:
        raise HTTPException(500, "点赞操作失败")
    return result


@favRouter.get("/like/status/{id}", summary="获取当前用户点赞状态")
async def like_status(id: int, phone: auth_phone, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")

    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")

    return {
        "msg": "获取成功",
        "is_liked": await query_like_status(id, rid, db),
    }


@favRouter.post("/like/status/batch", summary="批量获取当前用户点赞状态")
async def like_status_batch(body: LikeBatchStatusBody, phone: auth_phone, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")

    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")

    return {
        "msg": "获取成功",
        "items": await query_like_status_map(body.ids, rid, db),
    }


@favRouter.get("/like/count/{id}", summary="获取博客点赞数")
async def like_count(id: int, db: db_dependency):
    count = await query_like_count(id, db)
    if count is None:
        raise HTTPException(404, "目标不存在或不可点赞")
    return {
        "msg": "获取成功",
        "like_count": count,
    }