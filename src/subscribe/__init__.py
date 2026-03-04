import strawberry


@strawberry.type
class BlogSnapshot:
    blogId: int
    title: str
    authorId: int


@strawberry.type
class EventSnapshot:
    eventType: str
    payload: str


