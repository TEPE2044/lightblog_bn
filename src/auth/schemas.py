# 数据库模型
from pydantic import BaseModel
from pydantic import Field


# ...是 Ellipsis的简写，表示该字段是必需的
# 表单数据模型
class AccountFormData(BaseModel):
    account: str = Field(..., min_lenth=11, max_length=11, description="账号")
    password: str = Field(..., min_lenth=6, description="密码")


class SMSFormData(BaseModel):
    codeActive: bool = Field(..., description="短信验证码")
    phone: str = Field(..., min_lenth=11, max_length=11, description="手机号")


class PhoneFormData(BaseModel):
    phone: str = Field(..., min_lenth=11, max_length=11, description="手机号")
    code: str = Field(..., min_lenth=4, max_length=4, description="验证码")
    iaccept: bool = Field(..., description="是否同意用户协议和隐私政策")


class ResetData(BaseModel):
    email: str = Field(...)
    old_phone: str = Field(...)
    new_phone: str = Field(...)
