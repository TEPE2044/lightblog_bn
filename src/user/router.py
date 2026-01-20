from fastapi import APIRouter, Request, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader

from src.database import db_dependency, rd_dependency
from src.user.services import query_user, auth_current_user

userRouter = APIRouter(prefix="/user", tags=['用户模块'])

security = HTTPBearer()
x_payload = APIKeyHeader(name="X-Payload")


# userCRUD

@userRouter.get("/profile", summary="获取用户个人信息获取接口")
async def get_user_profile(db: db_dependency, rd: rd_dependency, request: Request):
    phone = await auth_current_user(request, rd)
    print(phone)
    # phone 是 手机号字符串 或 False
    if phone is False:
        raise HTTPException(status_code=401, detail="登陆状态已失效，请重新登录")

    username, avatar, gender, type = await query_user(phone, db)
    # sex字段优化成gender
    userInfo = {
        "username": username,
        "avatar": avatar,
        "gender": gender,
        "type": type
    }
    return {"status": "200", "msg": "用户信息获取成功", "data": userInfo}


@userRouter.post("/profile", summary="设置用户个人信息")
async def post_user_profile():
    return {"status": "200", "msg": "用户信息获取成功", "data": {}}


# 头像上传、签名修改、男还是女的、用户名
@userRouter.patch("/profile", summary="更新用户个人信息")
async def update_user_profile():
    return {"status": "200", "msg": "用户信息更新成功", "data": {}}
