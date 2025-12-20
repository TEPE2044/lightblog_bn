from strawberry.types import Info

from src.user.gql.types import UserGQL
from src.user.services import auth_current_user, query_user


async def resolve_me(info: Info) -> "UserGQL":
    request = info.context["request"]  # FastAPI Request
    db = info.context["db"]  # 依赖注入
    rd = info.context["rd"]

    user_id = await auth_current_user(request, rd)
    if not user_id:
        raise Exception("登陆状态已失效，请重新登录")

    user_orm = await query_user(user_id, db)
    if not user_orm:
        raise Exception("用户不存在")

    return UserGQL(id=user_orm.id,
                   nickname=user_orm.username,
                   avatar=user_orm.avatar)
