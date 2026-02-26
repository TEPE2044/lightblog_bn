import strawberry


@strawberry.type
class Blog:
    cover: list[str]
    title: str
    author: str
    tags: list[str]


@strawberry.type
class User:
    avatar: str
    username: str
    signature: str
