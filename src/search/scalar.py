import json

import strawberry
from strawberry.fastapi import GraphQLRouter

from src.database.redis_train import train
from src.subscribe import BlogSnapshot


# Info是啥


@strawberry.type
class Query:
    @strawberry.field
    def temp(self) -> str:
        return 'nihao'


@strawberry.type
class Mutation:
    @strawberry.mutation(description='手动造一条博客事件（给所有粉丝推送）')
    async def publish_blog_event(self, blog_id: int, title: str, author_id: int) -> BlogSnapshot:
        # 1. 先假装写库（你原来 insert 的地方）
        # await db.execute(...)

        # 2. 直接往全局频道丢（测试阶段先广播，后面再改私人频道）
        await train.publish("BLOG_NEW", json.dumps({
            "blogId": blog_id,
            "title": title,
            "authorId": author_id
        }))
        return BlogSnapshot(blog_id, title, author_id)


search_schema = strawberry.Schema(query=Query,mutation=Mutation)
searchRouter = GraphQLRouter(search_schema, path="gql/subql")
