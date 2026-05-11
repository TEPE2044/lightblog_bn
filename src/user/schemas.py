from typing import Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    username: str = Field(min_length=1, max_length=30)
    gender: int = Field(ge=0, le=2)  # 0:未知，1:男，2:女
    signature: str = Field(max_length=30)
    avatarURL: Optional[str]


class VisitData(BaseModel):
    default_v: str
    home_v: str
    post_v: str
    fav_v: str
