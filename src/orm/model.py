# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, Enum, DateTime, func, text, Integer, Identity, TEXT, Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID  # 数据库层仍用 PG 的 UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from src.orm import UserTypeEnum, StatusEnum, GenderEnum, BlogEnum, BlogStateEnum


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

    gender: Mapped[GenderEnum] = mapped_column(
        Enum(GenderEnum),
        default=GenderEnum.unknown,
        server_default='unknown',
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
        default=StatusEnum.active,
        nullable=False,
        comment="0正常 1危险 2封禁"
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
        nullable=True,
        comment="用户头像URL"
    )

    signature: Mapped[str | None] = mapped_column(
        String(255),
        server_default='这个人很懒，什么都没留下',
        nullable=False,
        comment="用户个性签名"
    )


# 关系表无需新建类 - Tag 和 Blog n*n
blogs_tags = Table(
    "blogs_tags",
    Base.metadata,
    Column(
        "blog_id",
        ForeignKey("blogs.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Blog ID"
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Tag ID"
    ),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1, increment=1, cycle=False),
        unique=True,
        index=True,
        nullable=False,
        primary_key=True,
        comment="标签id"
    )

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    blogs: Mapped[List["Blog"]] = relationship(
        secondary=blogs_tags,
        back_populates="tags"
    )

class Blog(Base):
    __tablename__ = "blogs"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1, increment=1, cycle=False),
        unique=True,
        index=True,
        nullable=False,
        primary_key=True,
        comment="博客id"
    )

    type: Mapped[BlogEnum] = mapped_column(
        Enum(BlogEnum),
        default=BlogEnum.draft,
        nullable=False,
        comment="0草稿 1正式"
    )

    state: Mapped[BlogStateEnum] = mapped_column(
        Enum(BlogStateEnum),
        default=BlogStateEnum.normal,
        nullable=False,
        comment="0正常 1已删除 2被封禁"
    )

    title: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        comment="博客标题"
    )

    content: Mapped[text] = mapped_column(
        TEXT,
        nullable=False,
        comment="博客内容"
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
    # 外键
    tags: Mapped[List[Tag]] = relationship(
        secondary=blogs_tags,
        back_populates="blogs"
    )
