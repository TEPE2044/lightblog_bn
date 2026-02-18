from typing import Optional

from pydantic import BaseModel, Field


class AudioBase(BaseModel):
    isOriginal: bool = Field(...)
    name: str = Field(..., max_length=50)
    desc: Optional[str]
    coverURL: str
    audioURL: str
