from fastapi import APIRouter

authRouter = APIRouter(tags=['用户模块'])


@authRouter.get("/login")
async def login():
    return {"message": "登录接口"}

