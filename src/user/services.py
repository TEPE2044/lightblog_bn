from http.client import HTTPException
from typing import Tuple, Dict

from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import dependency

from src.config import settings
from src.database import rd_dependency
from src.orm import UserTypeEnum
from src.orm.model import User
from src.utils.aes_client import decrypt_phone
from src.utils.jwt_client import ALGORITHM


async def auth_current_user(request, rd: rd_dependency) -> bool | str:
    rcode_h = request.headers.get("authorization") or ""
    print(rcode_h)
    if not rcode_h.lower().startswith("bearer "):
        return False
    rcode = rcode_h[7:]
    payload = request.headers.get("x-payload") or ""
    # 解码payload，然后比较phone和redis中的phone是否一致
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


async def query_user(phone: str, db: dependency) -> UserTypeEnum | None:
    return await db.scalar(select(User.type, User.username, User.reks_id, User.avatar).where(User.phone == phone))
