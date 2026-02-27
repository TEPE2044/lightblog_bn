import strawberry



@strawberry.input
class Paging:
    page: int
    page_size: int


@strawberry.type
class Author:
    id: int
    username: str
    avatar: str


@strawberry.type
class Blog:
    id: int
    cover: str
    title: str
    type: str
    author: Author
    created_at: str



@strawberry.type
class User:
    avatar: str
    username: str
    signature: str
