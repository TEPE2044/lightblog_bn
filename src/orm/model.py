# 模型
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Enum, DateTime, func, text
from sqlalchemy.types import String
from src.database import Base
from src.orm import SexEnum, UserTypeEnum, StatusEnum


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"), comment="用户ID")
    phone = Column(String(20), unique=True, index=True, nullable=False, comment="手机号")
    hashed_password = Column(String(255), nullable=True, comment="哈希密码")
    username = Column(String(35), index=True, nullable=False, comment="用户名")
    sex = Column(Enum(SexEnum), default=SexEnum.unknown, nullable=False, comment="0未知 1男 2女")
    email = Column(String(320), unique=True, index=True, nullable=True, comment="电子邮箱")
    type = Column(Enum(UserTypeEnum), default=UserTypeEnum.ordinary, nullable=False, comment="0用户 1管理员 2超管")
    status = Column(Enum(StatusEnum), default=StatusEnum.inactive, nullable=False, comment="0正常 1禁用 2未激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
                        comment="更新时间")
    deleted_at = Column(DateTime(timezone=True), index=True, nullable=True, comment="软删除时间 NULL=未删除")
