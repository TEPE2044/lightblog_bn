from typing import Optional

import strawberry


@strawberry.type
class UserProfile:
    username: str
    avatar: Optional[str]
    gender: str
    type: str
    sign: str
