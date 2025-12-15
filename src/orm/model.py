# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, func, text, Integer, Identity
from sqlalchemy.dialects.postgresql import UUID as PG_UUID  # 数据库层仍用 PG 的 UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
from src.orm import SexEnum, UserTypeEnum, StatusEnum


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="用户UUID"
    )

    reks_id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1, increment=1, cycle=False),
        unique=True,
        index=True,
        nullable=False,
        comment="用户通用id"
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="手机号"
    )

    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="哈希密码"
    )

    username: Mapped[str] = mapped_column(
        String(35),
        index=True,
        nullable=False,
        comment="用户名"
    )

    sex: Mapped[SexEnum] = mapped_column(
        Enum(SexEnum),
        default=SexEnum.unknown,
        nullable=False,
        comment="0未知 1男 2女"
    )

    email: Mapped[str | None] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=True,
        comment="电子邮箱"
    )

    type: Mapped[UserTypeEnum] = mapped_column(
        Enum(UserTypeEnum),
        default=UserTypeEnum.ordinary,
        nullable=False,
        comment="0用户 1管理员 2超管"
    )

    status: Mapped[StatusEnum] = mapped_column(
        Enum(StatusEnum),
        default=StatusEnum.inactive,
        nullable=False,
        comment="0正常 1禁用 2未激活"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=True,
        comment="软删除时间 NULL=未删除"
    )

    avatar: Mapped[str | None] = mapped_column(
        String(255),
        server_default='https://projeck.obs.cn-south-1.myhuaweicloud.com/UserIcon/1/20250706135900_avatar.jpg',
        nullable=False,
        comment="用户头像URL"
    )
