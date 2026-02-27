from datetime import datetime
from typing import List

import strawberry


@strawberry.type
class BlogResult:
    title: str
    cover: str
    tags: List[str]
    created_at: datetime
