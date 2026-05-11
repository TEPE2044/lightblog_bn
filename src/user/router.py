from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, APIKeyHeader

from src.database import db_dependency, rd_dependency
from src.user.schemas import UserProfile, VisitData
from src.user.services import (
    query_user,
    query_user_by_rid,
    auth_phone,
    update_user_profile,
    query_safety_level, query_user_visibility, query_user_visibility_by_id, update_visits,
)
from src.utils.Rback import rback

userRouter = APIRouter(prefix="/user", tags=['用户模块'])
security = HTTPBearer()
x_payload = APIKeyHeader(name="X-Payload")


@userRouter.get("/safety-level", summary="用户安全等级")
async def get_safety_level(db: db_dependency, phone: auth_phone):
    if phone is False:
        raise HTTPException(status_code=401, detail="登陆状态已失效，请重新登录")

    level = await query_safety_level(db, phone)
    return {"status": 200, "level": level}


# userCRUD
@userRouter.get("/profile", summary="获取用户个人信息获取接口")
async def get_user_profile(db: db_dependency, phone: auth_phone):
    print(phone)
    # phone 是 手机号字符串 或 False
    if phone is False:
        raise HTTPException(status_code=401, detail="登陆状态已失效，请重新登录")

    reks_id, username, avatar, gender, type, sign = await query_user(phone, db)
    userInfo = {
        "reks_id": reks_id,
        "username": username,
        "avatar": avatar,
        "gender": gender,
        "type": type,
        "sign": sign
    }
    return {"status": "200", "msg": "用户信息获取成功", "data": userInfo}


@userRouter.get("/profile/{rid}", summary="根据用户ID获取公开信息")
async def get_user_profile_by_rid(rid: int, db: db_dependency):
    row = await query_user_by_rid(rid, db)
    if row is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    reks_id, username, avatar, gender, type_, sign = row
    userInfo = {
        "reks_id": reks_id,
        "username": username,
        "avatar": avatar,
        "gender": gender,
        "type": type_,
        "sign": sign,
    }
    return {"status": "200", "msg": "用户信息获取成功", "data": userInfo}


# @userRouter.get("/profile", summary="获取用户个人信息获取接口")
# async def get_user_profile(db: db_dependency, rd: rd_dependency, request: Request):
#     phone = await auth_current_user(request, rd)
#     print(phone)
#     # phone 是 手机号字符串 或 False
#     if phone is False:
#         raise HTTPException(status_code=401, detail="登陆状态已失效，请重新登录")
#
#     username, avatar, gender, type = await query_user(phone, db)
#     # sex字段优化成gender
#     userInfo = {
#         "username": username,
#         "avatar": avatar,
#         "gender": gender,
#         "type": type
#     }
#     return {"status": "200", "msg": "用户信息获取成功", "data": userInfo}


@userRouter.post("/profile", summary="设置用户个人信息")
async def post_user_profile(db: db_dependency, phone: auth_phone, data: UserProfile):
    if phone is False:
        raise HTTPException(status_code=401, detail="登陆状态已失效，请重新登录")

    if data is None:
        return {"status": 200, "msg": "无事发生"}
    print("....")
    is_update = await update_user_profile(data, db, phone)
    try:
        if is_update is True:
            return {"status": "200", "msg": "用户信息设置成功"}
        else:
            raise HTTPException(status_code=400, detail="用户信息设置失败")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="用户信息设置失败")


# 获取当前用户的访问状态
@userRouter.get("/visit", summary="获取当前用户访问状态")
async def get_user_visibility(db: db_dependency, phone: auth_phone):
    if phone is False:
        raise HTTPException(status_code=401, detail="登陆状态已失效，请重新登录")
    try:
        res = await query_user_visibility(db, phone)
        print(res)
        if res:
            return rback(200, '获取成功', res)
        else:
            raise HTTPException(404, '无该用户信息')
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@userRouter.get("/visit/{id}", summary="获取某个用户的访问状态")
async def get_user_visibility_by_id(id: int, db: db_dependency):
    try:
        res = await query_user_visibility_by_id(db, id)
        if res:
            return rback(200, "获取成功", res)
        else:
            raise HTTPException(404, "不存在该用户")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@userRouter.post("/visit/update", summary="更新访问状态")
async def update_visit(db: db_dependency, phone: auth_phone, data: VisitData):
    if phone is False:
        raise HTTPException(status_code=401, detail="登陆状态已失效，请重新登录")
    try:
        res = await update_visits(db, data, phone)
        if res:
            return rback(200, "获取成功", res)
        else:
            raise HTTPException(404, "不存在该用户")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
