import hashlib
from typing import Dict

from fastapi import UploadFile
from sqlalchemy import select, and_, insert, func
from src.blog.schemas import BlogData
from src.database import db_dependency
from src.orm.model import Blog, blogs_tags, Tag, Gallery
from sqlalchemy.dialects.postgresql import insert as prt  # 用 pg 的 upsert


# 获取博客
async def get_blogs(id: int, db: db_dependency) -> Dict | None:
    # 满足条件：是发布的、是正常的、有id的
    try:
        stmt = (select(Blog).where(
            and_(
                Blog.type == 'publish',
                Blog.state == 'normal',
                Blog.id == id
            )
        ))
        # 只可有一条，但是允许是空的
        blog = (await db.execute(stmt)).scalar_one_or_none()
        if not blog:
            return None
        print(blog.title)
        return {
            "title": blog.title,
            "content": blog.content,
            "updated_at": blog.updated_at,
            "type": blog.type
        }
    except Exception as e:
        print(e)
        return None


async def upsert_blog(data: BlogData, rid: int, db: db_dependency) -> bool:
    try:
        # 先插入title和content，并且最终返回插入后的内容blog
        insert_blog = prt(Blog).values(title=data.title, content=data.content,
                                           rid=rid).returning(Blog)
        blog = (await db.execute(insert_blog)).scalar_one()
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


# TODO:获取一个用户的所有博客，包括草稿箱，可能要进行分页查询
async def query_user_blogs(rid: int, db: db_dependency) -> list[Blog] | None:
    try:
        join_blog = select(Blog).where(Blog.rid == rid).order_by(Blog.updated_at.desc())
        blogs = (await db.execute(join_blog)).scalars().all()
        return blogs
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
