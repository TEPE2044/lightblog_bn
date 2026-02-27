from datetime import datetime
from typing import List

import strawberry


@strawberry.type
class Blog:
    id: int
    cover: str
    title: str
    author: str
    type: str
    created_at: datetime


@strawberry.type
class User:
    avatar: str
    username: str
    signature: str
