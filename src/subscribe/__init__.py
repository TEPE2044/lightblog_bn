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


@strawberry.type
class FollowStatsSnapshot:
    followingCount: int
    followerCount: int


@strawberry.type
class FollowUserSnapshot:
    rid: int
    username: str
    avatar: str | None
    signature: str | None


