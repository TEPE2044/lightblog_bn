# 数据库模型
from pydantic import BaseModel


# 表单数据模型
class AccountFormData(BaseModel):
    account: str
    password: str


class SMSFormData(BaseModel):
    codeActive: bool
    phone: str


class PhoneFormData(BaseModel):
    phone: str
    code: str
    iaccept:bool
