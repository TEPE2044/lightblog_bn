from jose import jwt
from redis.asyncio import Redis

from src.config import settings
from src.utils.aes_client import decrypt_phone
from src.utils.jwt_client import ALGORITHM


# gql鉴权
async def auth_current_user(
        headers: dict[str, str],
        rd: Redis,
) -> bool | str:
    normalized = {str(k).lower(): v for k, v in headers.items()}

    header_rcode = normalized.get("authorization") or ""
    if not header_rcode.lower().startswith("bearer "):
        return False
    rcode = header_rcode[7:]

    payload = normalized.get("x-payload") or ""
    try:
        data = jwt.decode(payload, settings.jwt_secret, algorithms=[ALGORITHM])
    except Exception:
        return False

    phone_in_jwt: str = await decrypt_phone(data.get("sub"))
    phone_in_redis = await rd.get(f"sess:{rcode}")

    compare_phone = str(phone_in_jwt) == str(phone_in_redis)
    return phone_in_jwt if compare_phone else False
