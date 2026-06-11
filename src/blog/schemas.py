from typing import List, Optional

from pydantic import BaseModel, Field


class BlogData(BaseModel):
    title: str = Field(..., min_length=1, max_length=30)
    content: str = Field(..., min_length=1)
    cover: List[str] = Field(..., max_length=3)
    tags: List[str] = Field(..., max_length=5)
    music_id: Optional[int] = None


class PostData(BaseModel):
    title: str = Field(..., min_length=1, max_length=30)
    content: str = Field(..., min_length=1)
    cover: List[str] = Field(..., max_length=3)
    tags: List[str] = Field(..., max_length=5)
    ste: int = Field(...)  # 0-draft 1-publish


class UpdateData(BaseModel):
    blog_id: int = Field(...)
    title: str = Field(..., min_length=1, max_length=30)
    content: str = Field(..., min_length=1)
    cover: List[str] = Field(..., max_length=3)
    tags: List[str] = Field(..., max_length=5)


class CursorPageInput(BaseModel):
    cursor: Optional[int] = None
    limit: int = Field(default=9, ge=1, le=30)
