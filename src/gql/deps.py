from jose import jwt
from redis.asyncio import Redis

from src.config import settings
from src.utils.aes_client import decrypt_phone
from src.utils.jwt_client import ALGORITHM
from strawberry import Info


# 整理上下文
def _collect_headers(info: Info) -> dict[str, str]:
    headers: dict[str, str] = {}
    context = info.context if isinstance(info.context, dict) else {}
    # 取HTTP场景的rcode和jwt
    # 为什么要取? Query&Mutation:我呸！你怎么这么自私！
    request = context.get("request")
    if request is not None and hasattr(request, "headers"):
        headers.update({str(k): str(v) for k, v in request.headers.items()})
    # 
    websocket = context.get("ws") or context.get("websocket")
    if websocket is not None and hasattr(websocket, "headers"):
        headers.update({str(k): str(v) for k, v in websocket.headers.items()})
    # 真正取数据
    params = context.get("connection_params")
    if isinstance(params, dict):
        headers.update({str(k): str(v) for k, v in params.items()})

    return headers


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
