from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, APIKeyHeader

from src.database import db_dependency, rd_dependency
from src.user.schemas import UserProfile
from src.user.services import query_user, auth_phone, update_user_profile

userRouter = APIRouter(prefix="/user", tags=['用户模块'])

security = HTTPBearer()
x_payload = APIKeyHeader(name="X-Payload")


# userCRUD
@userRouter.get("/profile", summary="获取用户个人信息获取接口")
async def get_user_profile(db: db_dependency, phone: auth_phone):
    print(phone)
    # phone 是 手机号字符串 或 False
    if phone is False:
        raise HTTPException(status_code=401, detail="登陆状态已失效，请重新登录")

    username, avatar, gender, type, sign = await query_user(phone, db)
    userInfo = {
        "username": username,
        "avatar": avatar,
        "gender": gender,
        "type": type,
        "sign": sign
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
