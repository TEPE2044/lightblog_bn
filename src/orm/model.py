# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import String, Enum, DateTime, func, text, Integer, Identity, TEXT, Table, Column, \
    ForeignKey, Boolean, \
    true, JSON, CheckConstraint, UniqueConstraint, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID  # 数据库层仍用 PG 的 UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
from src.orm import UserTypeEnum, StatusEnum, GenderEnum, ImgEnum, BlogStateEnum, BlogEnum


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
        comment="0正常 1危险 2封禁 3注销"
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

    playlists: Mapped[list["PlayList"]] = relationship(back_populates='creator')

    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", foreign_keys="Contact.user_id", back_populates="user"
    )
    followers: Mapped[list["Contact"]] = relationship(
        "Contact", foreign_keys="Contact.followed_user_id", back_populates="followed_user"
    )
    conversations_as_a: Mapped[list["Conversation"]] = relationship(
        "Conversation", foreign_keys="Conversation.user_a_id", back_populates="user_a"
    )
    conversations_as_b: Mapped[list["Conversation"]] = relationship(
        "Conversation", foreign_keys="Conversation.user_b_id", back_populates="user_b"
    )
    sent_messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="sender"
    )


# 关系表无需新建类 - Tag 和 Blog n*n
# 没业务字段用 Table，有业务字段就建类
# 显式  Table  定义，没有对应的 ORM 类, 查询时使用.c
blogs_tags = Table(
    "blogs_tags",
    Base.metadata,
    Column(
        "blog_id",
        ForeignKey("blogs.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        comment="Blog ID"
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
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

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )

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
        default=BlogEnum.blog,
        nullable=False,
        comment="0音乐博客 1博客"
    )

    state: Mapped[BlogStateEnum] = mapped_column(
        Enum(BlogStateEnum),
        default=BlogStateEnum.publish,
        nullable=False,
        comment="0草稿 1正常 2已删除 3被封禁"
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

    rid: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
        comment="用户通用id"
    )

    cover: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        server_default='["https://picsum.photos/seed/picsum/200/300"]',
        comment="封面URL集合"
    )

    # 外键
    tags: Mapped[List[Tag]] = relationship(
        secondary=blogs_tags,
        back_populates="blogs"
    )


class Gallery(Base):
    __tablename__ = 'gallery'
    id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1, increment=1, cycle=False),
        unique=True,
        index=True,
        nullable=False,
        primary_key=True,
        comment="图片id"
    )

    type: Mapped[ImgEnum] = mapped_column(
        Enum(ImgEnum),
        default=ImgEnum.file,
        nullable=False,
        comment="0文件图片 1普通图片"
    )

    rid: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
        comment="用户通用id"
    )

    url: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="图片链接"
    )

    alt: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="图片描述"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )

    md5: Mapped[str | None] = mapped_column(
        String(32),
        index=True,
        unique=True,
        nullable=True,
        comment="文件哈希"
    )


class PlaylistMusic(Base):
    __tablename__ = 'playlists_music'

    # 指向歌单：级联删除
    playlist_id: Mapped[int] = mapped_column(
        ForeignKey('playlist.id', ondelete='CASCADE'),
        primary_key=True
    )

    # 指向歌曲：普通外键，**不开级联**
    # ← 不写 ondelete
    music_id: Mapped[int] = mapped_column(
        ForeignKey('music.id'),
        primary_key=True
    )

    sort_order: Mapped[int] = mapped_column(default=0)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    playlist: Mapped["PlayList"] = relationship(back_populates='tracks')


class Music(Base):
    __tablename__ = 'music'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment="音频id"
    )
    name: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False, comment="音频名称"
    )
    rid: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(User.reks_id),
        index=True,
        nullable=False,
        comment="用户通用id"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    state: Mapped[BlogStateEnum] = mapped_column(
        Enum(BlogStateEnum, native_enum=False),
        default=BlogStateEnum.publish,
        nullable=True,
        comment="0草稿 1发布 2已删除 3被封禁"
    )
    original: Mapped[bool] = mapped_column(
        Boolean,
        server_default=true(),
        nullable=False,
        comment="是否原创"
    )
    cover: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default='https://picsum.photos/seed/picsum/200/300',
        comment="封面URL"
    )
    audio: Mapped[str] = mapped_column(String, nullable=True, comment="音频URL")
    desc: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="简介")


class PlayList(Base):
    __tablename__ = 'playlist'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="歌单id")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='歌单标题')
    cover: Mapped[str | None] = mapped_column(String(500), comment='封面URL')
    desc: Mapped[str | None] = mapped_column(String(500), comment='简介')
    is_private: Mapped[bool] = mapped_column(default=False, comment='是否私密')
    rid: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(User.reks_id),
        index=True,
        nullable=False,
        comment="用户通用id"
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now())
    # 关系
    creator: Mapped[User] = relationship(back_populates='playlists')
    tracks: Mapped[list[PlaylistMusic]] = relationship(back_populates='playlist', cascade='all, delete-orphan')


class Blog_Music(Base):
    __tablename__ = "blogs_music"
    blog_id: Mapped[int] = mapped_column(
        ForeignKey("blogs.id", ondelete="CASCADE"),
        primary_key=True
    )
    music_id: Mapped[int] = mapped_column(
        ForeignKey("music.id", ondelete="RESTRICT"),
        primary_key=True
    )
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("user_id", "followed_user_id", name="uq_contacts_pair"),
        CheckConstraint("user_id <> followed_user_id", name="ck_contacts_not_self"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="联系人记录UUID",
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.reks_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="关注者通用ID(reks_id)",
    )

    followed_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.reks_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="被关注者通用ID(reks_id)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="关注时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )

    last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="关注动态已读游标时间",
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="contacts",
    )

    followed_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[followed_user_id],
        back_populates="followers",
    )


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint("user_a_id <> user_b_id", name="ck_conversations_not_self"),
        # 防止 A-B 与 B-A 重复会话
        Index(
            "uq_conversations_user_pair_norm",
            text("LEAST(user_a_id, user_b_id)"),
            text("GREATEST(user_a_id, user_b_id)"),
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="会话UUID",
    )

    user_a_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="会话用户A",
    )

    user_b_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="会话用户B",
    )

    last_message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="最后一条消息预览",
    )

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=True,
        comment="最后消息时间",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )

    user_a: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_a_id],
        back_populates="conversations_as_a",
    )

    user_b: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_b_id],
        back_populates="conversations_as_b",
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", text("created_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="消息UUID",
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="会话UUID",
    )

    sender_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="发送者UUID",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="文本消息内容",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="发送时间",
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=True,
        comment="软删除时间 NULL=未删除",
    )

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )

    sender: Mapped["User"] = relationship(
        "User",
        back_populates="sent_messages",
    )
