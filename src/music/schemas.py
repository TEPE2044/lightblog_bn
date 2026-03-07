from typing import Optional

from pydantic import BaseModel, Field


class AudioBase(BaseModel):
    isOriginal: bool = Field(...)
    name: str = Field(..., max_length=50)
    desc: Optional[str]
    coverURL: str
    audioURL: str


class CursorPageInput(BaseModel):
    cursor: Optional[int] = None
    limit: int = Field(default=9, ge=1, le=30)
