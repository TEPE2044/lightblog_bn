from fastapi import APIRouter

from src.auth.schemas import EmailFormData
from src.database import db_dependency

authRouter = APIRouter(tags=['用户模块'])


@authRouter.post("/email_login")
async def login(front: EmailFormData,db: db_dependency):
    return {"message": "登录接口"}


@authRouter.post("/phone_login")
async def login(front: int,db: db_dependency):
    return {"message": "手机号登录接口"}

