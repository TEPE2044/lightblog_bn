from fastapi import APIRouter, Request, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader

from src.database import db_dependency, rd_dependency
from src.user.services import query_user, auth_current_user

userRouter = APIRouter(prefix="/user", tags=['用户模块'])

security = HTTPBearer()
x_payload = APIKeyHeader(name="X-Payload")


# userCRUD

# 改成GraphQL接口,此接口保留备用
@userRouter.get("/profile", summary="获取用户个人信息获取接口")
async def get_user_profile(db: db_dependency, rd: rd_dependency, request: Request):
    isIt = await auth_current_user(request, rd)
    print(isIt)
    # isIt 是 手机号字符串 或 False
    if isIt is False:
        raise HTTPException(status_code=401, detail="登陆状态已失效，请重新登录")

    username, avatar, sex, type = await query_user(isIt, db)
    # sex字段优化成gender
    userInfo = {
        "username": username,
        "avatar": avatar,
        "sex": sex,
        "type": type
    }
    return {"status": "200", "msg": "用户信息获取成功", "data": userInfo}


@userRouter.post("/profile", summary="设置用户个人信息")
async def post_user_profile():
    return {"status": "200", "msg": "用户信息获取成功", "data": {}}


@userRouter.patch("/profile", summary="更新用户个人信息")
async def update_user_profile():
    return {"status": "200", "msg": "用户信息更新成功", "data": {}}

# TODO: 实现头像上传功能
@userRouter.post("/upload-avatar", summary="上传用户头像")
async def upload_user_avatar():
    pass
