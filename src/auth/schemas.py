# 数据库模型
from pydantic import BaseModel

# 表单数据模型
class EmailFormData(BaseModel):
    account: str
    hash_password: str

