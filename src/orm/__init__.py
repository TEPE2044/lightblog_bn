from enum import Enum


class GenderEnum(int, Enum):
    unknown = 0
    male = 1
    female = 2


class UserTypeEnum(int, Enum):
    ordinary = 0
    admin = 1
    supreme = 2


class StatusEnum(int, Enum):
    active = 0
    danger = 1
    block = 2
