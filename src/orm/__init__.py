from enum import Enum


# 编写枚举类型前注意：
# 继承顺序 int, Enum 表示枚举成员同时具有整数类型行为和枚举行为，成员既是 Enum 成员又可当作 int 使用（可比较、参与算术等）
# 纯  Enum  → 枚举成员只是“标签”，不再是数字，所有数值操作都得通过  .value
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


class BlogEnum(int, Enum):
    draft = 0
    publish = 1


# 后期加一个hidden限制
class BlogStateEnum(int, Enum):
    normal = 0
    delete = 1
    ban = 2  # 服务于后台接口
