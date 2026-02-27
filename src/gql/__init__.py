import strawberry


@strawberry.type
class HTTPResult:
    status: int
    msg: str
