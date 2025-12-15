from fastapi import APIRouter, Request, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.database import db_dependency, rd_dependency
from src.user.services import query_user, auth_current_user

userRouter = APIRouter(prefix="/user", tags=['用户模块'])

security = HTTPBearer()


# userCRUD

@userRouter.get("/profile", summary="获取用户个人信息获取接口")
async def get_user_profile(db: db_dependency, rd: rd_dependency, request: Request,):
    isIt = await auth_current_user(request, rd)
    print(isIt)
    if isIt is False:
        raise HTTPException(status_code=401, detail="登陆状态已失效，请重新登录")

    userInfo = await query_user(isIt, db)
    print(userInfo)
    return {"status": "200", "msg": "用户信息获取成功", "data": {userInfo}}


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
