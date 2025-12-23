import secrets
from datetime import datetime, timedelta

from jose import jwt

from src.config import settings
from src.database import rd_dependency
from src.utils.aes_client import encrypt_phone

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 30


async def create_access_token(phone: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    phone = await encrypt_phone(phone)
    token = jwt.encode({"sub": phone, "exp": expire}, settings.jwt_secret, algorithm=ALGORITHM)
    return token


async def create_reks_code() -> str:
    return secrets.token_urlsafe(32)


async def create_all_tokens(phone: str, rd: rd_dependency) -> dict:
    # 生成token返回前端
    payload = await create_access_token(phone)
    reks_code = await create_reks_code()
    await rd.setex(f"sess:{reks_code}", ACCESS_TOKEN_EXPIRE_MINUTES, phone)
    return {
        "payload": payload,
        "rcode": reks_code
    }
