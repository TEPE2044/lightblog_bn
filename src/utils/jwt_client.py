from datetime import datetime, timedelta

from jose import jwt

from src.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 30


async def create_access_token(phone: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode({"sub": phone, "exp": expire}, settings.jwt_secret, algorithm=ALGORITHM)
    return token


async def create_test_token(phone: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=24)
    token = jwt.encode({"sub": phone, "exp": expire}, settings.jwt_secret, algorithm=ALGORITHM)
    return token
