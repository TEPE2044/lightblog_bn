from typing import List

from pydantic import BaseModel, Field


class BlogData(BaseModel):
    title: str = Field(..., min_length=1, max_length=30)
    content: str = Field(..., min_length=1)
    tags: List[str] = Field(..., max_length=5)



