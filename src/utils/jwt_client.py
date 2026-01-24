import secrets
from datetime import datetime, timedelta

from jose import jwt

from src.config import settings
from src.database import rd_dependency
from src.utils.aes_client import encrypt_phone

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 30


# 加强令牌配置项，应包含:iss，iat,exp,sub
async def create_access_token(phone: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    create_time = datetime.utcnow()
    phone = await encrypt_phone(phone)
    token = jwt.encode({"iss": 'TEPE2044', 'iat': create_time, "exp": expire, "sub": phone}, settings.jwt_secret,
                       algorithm=ALGORITHM)
    return token


async def create_reks_code() -> str:
    return secrets.token_urlsafe(32)


# 这里存在bug，假如有贱狗在前端删了我的rcode和payload，我redis还会残留 fixed
# 目前仅支持单点登录,但是JWT没法踢人下线，但是老token一旦请求就会显示过期
async def create_all_tokens(phone: str, rd: rd_dependency) -> dict:
    # 生成token返回前端
    # 先把钥匙找出来删掉
    try:
        old_code = await rd.get(f"loging:{phone}")
        await rd.delete(f"sess:{old_code}")
        print("已找到令牌并删除")
    except Exception as e:
        print("该手机号无旧令牌", e)
    payload = await create_access_token(phone)
    reks_code = await create_reks_code()
    await rd.setex(f"sess:{reks_code}", ACCESS_TOKEN_EXPIRE_MINUTES, phone)
    # 反向设置一把钥匙，在下次登录的时候，找到这把钥匙并删除
    await rd.setex(f"loging:{phone}", ACCESS_TOKEN_EXPIRE_MINUTES, reks_code)
    return {
        "payload": payload,
        "rcode": reks_code
    }


async def create_temp_code(rd: rd_dependency, email: str) -> str:
    tc = secrets.token_urlsafe(32)
    await rd.setex(f"temp{tc}", 300, email)
    return tc
