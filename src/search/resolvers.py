import json
from typing import List

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.scalars import JSON

from src.search.schemas import Paging
from src.search.services import query_blogs_paginated_by_content, query_blogs_paginated_by_tags, query_user_paginated, \
    query_music_paginated

'''
TODO:
2.电台搜索 
- 模糊搜索 
3.用户搜索
- 模糊搜索 
'''


@strawberry.type
class Query:
    @strawberry.field
    async def blog(self, content: str, p: Paging) -> JSON:
        result, total = await query_blogs_paginated_by_content(content, p.page, p.page_size)
        return {"data": result, "total": total}

    @strawberry.field
    async def blog_tag(self, tags: List[str], p: Paging) -> JSON:
        result, total = await query_blogs_paginated_by_tags(tags, p.page, p.page_size)
        return {"data": result, "total": total}

    @strawberry.field
    async def user(self, who: str, p: Paging) -> JSON:
        result, total = await query_user_paginated(who, p.page, p.page_size)
        return {"data": result, "total": total}

    @strawberry.field
    async def music(self, content: str, p: Paging) -> JSON:
        result, total = await query_music_paginated(content, p.page, p.page_size)
        return {"data": result, "total": total}


search = strawberry.Schema(query=Query)
searchRouter = GraphQLRouter(search, path="/gql/seaql")
