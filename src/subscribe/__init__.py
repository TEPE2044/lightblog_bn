import strawberry


@strawberry.type
class BlogSnapshot:
    blogId: int
    title: str
    authorId: int
