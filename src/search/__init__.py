from datetime import datetime

import strawberry


@strawberry.type
class BlogResult:
    title: str
    cover: str
    tags: list
    created_at: datetime
