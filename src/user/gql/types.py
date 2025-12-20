import strawberry
from typing import Optional


@strawberry.type
class UserGQL:
    id: int
    nickname: str
    avatar: Optional[str]
