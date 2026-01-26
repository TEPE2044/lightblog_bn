from functools import lru_cache
from typing import Annotated
from fastapi import Depends, Request
from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import dependency

from src.config import settings
from src.database import rd_dependency

from src.orm.model import User
from src.utils.aes_client import decrypt_phone
from src.utils.jwt_client import ALGORITHM


# 这里的Request是FastAPI的Request啊一直都是！
# 人太傻了怪不得一直踩坑
@lru_cache
async def auth_current_user(request: Request, rd: rd_dependency) -> bool | str:
    # rcode
    header_rcode = request.headers.get("authorization") or ""
    # print(header_rcode)
    if not header_rcode.lower().startswith("bearer "):
        return False
    rcode = header_rcode[7:]

    # 解码payload，然后比较phone和redis中的phone是否一致
    payload = request.headers.get("x-payload") or ""
    try:
        data = jwt.decode(payload, settings.jwt_secret, algorithms=[ALGORITHM])
    except Exception:
        return False

    phone_in_jwt: str = await decrypt_phone(data.get("sub"))
    phone_in_redis = await rd.get(f"sess:{rcode}")

    compare_phone = str(phone_in_jwt) == str(phone_in_redis)
    # print(compare_phone, phone_in_jwt, phone_in_redis)
    # 简写：当 compare_phone 为 True 返回 phone_in_jwt，否则返回 False
    return phone_in_jwt if compare_phone else False


auth_phone = Annotated[str | bool, Depends(auth_current_user)]


# scalar 查询单列，也就是只能查一个字段
# first 查多列
# one_or_none 想确保最多一条，否则算异常
async def query_user(phone: str, db: dependency):
    stmt = select(User.username, User.avatar, User.gender, User.type).where(User.phone == phone)
    # warning db操作是异步,first只是同步方法
    row = (await db.execute(stmt)).first()
    return row


async def query_user_rid(phone: str, db: dependency):
    stmt = select(User.reks_id).where(User.phone == phone)
    row = (await db.execute(stmt)).scalar_one_or_none()
    return row
