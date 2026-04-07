import strawberry


# Mutation需要input类型
@strawberry.input
class Notif:
    title: str
    content: str
