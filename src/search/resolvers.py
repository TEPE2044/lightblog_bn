from typing import List

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.scalars import JSON

from src.search.schemas import Paging
from src.search.services import query_blogs_paginated_by_content, query_blogs_paginated_by_tags

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
        return {"items": result, "total": total}

    @strawberry.field
    async def blog_tag(self, tags: List[str], p: Paging) -> JSON:
        result, total = await query_blogs_paginated_by_tags(tags, p.page, p.page_size)
        return {"items": result, "total": total}


search = strawberry.Schema(query=Query)
searchRouter = GraphQLRouter(search, path="/gql/seaql")
