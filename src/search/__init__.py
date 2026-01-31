import strawberry


@strawberry.type
class BlogResult:
    cover: list[str]
    title: str
    author: str
    tags: list[str]
