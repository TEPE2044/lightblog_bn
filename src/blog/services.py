import hashlib
from typing import Dict

from fastapi import UploadFile
from sqlalchemy import select, insert, func, and_
from sqlalchemy.orm import selectinload
from src.blog.schemas import BlogData
from src.database import db_dependency
from src.orm import BlogStateEnum
from src.orm.model import Blog, blogs_tags, Tag, Gallery, User
from sqlalchemy.dialects.postgresql import insert as prt  # 用 pg 的 upsert


# 获取博客
async def get_blogs(id: int, db: db_dependency) -> Dict | None:
    try:
        # Select the ORM Blog entity and eager-load tags to get a proper list[Tag]
        # options(selectinload(Blog.tags)) 会在查询博客时同时查询关联的标签，避免了N+1问题
        stmt = (select(Blog, User.username).options(selectinload(Blog.tags))
                .join(User, Blog.rid == User.reks_id).where(Blog.id == id))
        result = await db.execute(stmt)
        # 这玩意确实只返回一个，但是它的内容全都在这个对象里！不关scalar或者mappin的事
        row = result.one_or_none()
        if row is None:
            return None
        print(row)
        blog, author = row  # blog 是 ORM Blog 对象，author 是 username 字段
        # 结果：<src.orm.model.Blog object at 0x0000028208F4A5F0>
        # blog.tags is a list of Tag objects; return tag names
        tags = [t.name for t in getattr(blog, 'tags', [])]
        return {
            "content": blog.content,
            "title": blog.title,
            "tags": tags,
            "author": author  # 直接从 JOIN 结果拿
        }
    except Exception as e:
        print(e)
        return None


# 博客的插入和更新合成一个函数，id为0表示插入，否则更新
# is_draft=0为草稿，=1为正式博客
async def upsert_blog(data: BlogData, rid: int, blog_id: int, type_: int,
                      db: db_dependency) -> bool:
    try:
        # 先插入title和content，并且最终返回插入后的内容blog
        # id为0，新建博客/草稿
        if blog_id == 0:
            stmt = prt(Blog).values(title=data.title, content=data.content,
                                    rid=rid, cover=data.cover, type=type_).returning(Blog)
        # 不为0，更新博客/草稿
        else:
            stmt = (
                prt(Blog).values(id=blog_id, title=data.title, content=data.content,
                                 cover=data.cover)
                .on_conflict_do_update(index_elements=["id"]
                                       , set_={
                        'title': data.title, 'content': data.content, 'updated_at': func.now()})
                .returning(Blog))
        blog = (await db.execute(stmt)).scalar_one()
        blog_id = blog.id
        print(blog_id)
        # 如果有tags，插入tags到Tag表中，tags的格式['apple','egg','pen']

        insert_tag = prt(Tag).values([{"name": tag} for tag in set(data.tags)]
                                     ).on_conflict_do_update(index_elements=["name"],
                                                             set_={"updated_at": func.now()}
                                                             ).returning(Tag)
        # insert_tag = prt(Tag).values([{"name": tag} for tag in filter_tags]).returning(Tag)
        tags = (await db.execute(insert_tag)).all()
        # 提取成一个列表
        tag_ids = [t[0].id for t in tags]

        if blog_id != 0:
            # 删掉原先的标签
            await db.execute(
                blogs_tags.delete().where(blogs_tags.c.blog_id == blog_id)
            )

        # blogs_tags 合成大西瓜
        bt_collection = [{"blog_id": blog_id, "tag_id": tid} for tid in tag_ids]

        # 如果有bt_collection，写库
        if bt_collection:
            await db.execute(insert(blogs_tags).values(bt_collection))
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        print(e)
        return False


# TODO:分页查询
async def query_user_blogs(rid: int, state_: BlogStateEnum, db: db_dependency) -> list[Dict] | None:
    try:
        join_blog = select(Blog.id, Blog.cover, Blog.title, Blog.type, Blog.created_at).where(
            and_(Blog.rid == rid, Blog.state == state_)).order_by(Blog.updated_at.desc())
        blogs = (await db.execute(join_blog)).mappings().all()
        result = [
            {
                "id": blog.id,
                "cover": blog.cover,
                "title": blog.title,
                "type": blog.type,
                "created_at": blog.created_at
            }
            for blog in blogs
        ]
        print(result)
        return result
    except Exception as e:
        print(e)
        return None


# TODO:每日推荐
async def query_daily_blog(db: db_dependency) -> list[Dict] | None:
    try:
        stmt = (select(Blog.id, Blog.cover, Blog.title, Blog.type, Blog.created_at, User.username)
                .join(User, Blog.rid == User.reks_id).order_by(func.random()).limit(10))
        blogs = (await db.execute(stmt)).all()
        return [
            {
                "id": id_,  # ← 直接是变量名，清晰
                "cover": cover,
                "title": title,
                "type": type_,
                "created_at": created_at,
                "author": username
            }
            for id_, cover, title, type_, created_at, username in blogs  # ← 元组解包
        ]
    except Exception as e:
        print(e)
        return None


async def insert_into_gallery(rid: int, href: str, md5: str, db: db_dependency) -> bool:
    stmt = insert(Gallery).values(rid=rid, url=href, alt=f"reks-{href}", md5=md5).returning(
        Gallery.id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    await db.commit()
    print(row)
    if row is not None:
        return True
    else:
        return False


# 计算MD5 看不懂但是很牛逼
async def file_md5(upload_file: UploadFile) -> str:
    hasher = hashlib.md5()
    while chunk := await upload_file.read(8192):
        hasher.update(chunk)
    await upload_file.seek(0)
    return hasher.hexdigest()


# 查找重复项
async def query_by_hash(md5: str, db: db_dependency) -> str | None:
    stmt = select(Gallery.url).filter(Gallery.md5 == md5).limit(1)
    return (await db.execute(stmt)).scalar_one_or_none()
