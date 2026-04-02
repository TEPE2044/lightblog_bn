from typing import Optional

from pydantic import BaseModel, Field
from src.orm import MusicRelatedEnum, MusicTypeEnum


class AudioBase(BaseModel):
    isOriginal: bool = Field(...)
    name: str = Field(..., max_length=50)
    desc: Optional[str]
    coverURL: str
    audioURL: str
    type: MusicTypeEnum = Field(default=MusicTypeEnum.material)
    related: MusicRelatedEnum = Field(default=MusicRelatedEnum.normal)


class CursorPageInput(BaseModel):
    cursor: Optional[int] = None
    limit: int = Field(default=9, ge=1, le=30)
