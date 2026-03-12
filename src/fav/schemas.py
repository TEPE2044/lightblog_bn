from enum import Enum

from pydantic import BaseModel


class FavoriteTargetEnum(str, Enum):
	blog = "blog"
	music = "music"


class FavoriteToggleBody(BaseModel):
	target_type: FavoriteTargetEnum
	favorited: bool


class FavoriteBatchStatusBody(BaseModel):
	target_type: FavoriteTargetEnum
	ids: list[int]


class LikeToggleBody(BaseModel):
	liked: bool


class LikeBatchStatusBody(BaseModel):
	ids: list[int]
