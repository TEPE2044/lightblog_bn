from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from sqlalchemy import select, func

from src.blog.schemas import BlogData, CursorPageInput
from src.blog.services import (
    upsert_blog,
    query_user_blogs,
    insert_into_gallery,
    file_md5,
    query_by_hash,
    query_daily_blog,
    query_hot_blog_by_likes,
    query_user_blogs_cursor,
    query_hot_blog_cursor, soft_delete_blog, get_blog, _publish_draft,
)
from src.database import db_dependency
from src.deps import limiter
from src.orm import BlogStateEnum
from src.orm.model import User, Tag, blogs_tags, Blog
from src.user.services import auth_phone, query_user_rid
from src.utils.Rback import rback
from src.utils.obs_client import img_upload, pre_img_link
from src.utils.xss_clean import clean_content
from src.music.services import create_music_blog
from src.subscribe.services import publish_event_to_followers

blogRouter = APIRouter(prefix="/blog", tags=["博客模块"])


# 博客CRUD

# bug-fix:根目录下首先注册blog/{id}后，任何这个格式都会被要求提供参数
@blogRouter.get("/my-blog", summary="获取当前用户所有博客")
async def get_my_blog(phone: auth_phone, state_: BlogStateEnum, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        rid = await query_user_rid(phone, db)
        if rid is None:
            raise HTTPException(404, "用户不存在")
        my_blog = await query_user_blogs(rid, state_, db)
        if my_blog is not None:
            return {"msg": "获取成功", "blogs": my_blog}
    except Exception as e:
        print(e)
        raise HTTPException(404, "获取博客失败")


@blogRouter.post("/my-blog/cursor", summary="获取当前用户博客（游标分页）")
async def get_my_blog_cursor(phone: auth_phone, body: CursorPageInput, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        rid = await query_user_rid(phone, db)
        if rid is None:
            raise HTTPException(404, "用户不存在")

        page = await query_user_blogs_cursor(
            rid=rid,
            state_=BlogStateEnum.publish,
            cursor=body.cursor,
            limit=body.limit,
            db=db,
        )
        if page is None:
            raise HTTPException(404, "获取博客失败")
        return page
    except Exception as e:
        print(e)
        raise HTTPException(404, "获取博客失败")


@blogRouter.get("/user/{rid}", summary="获取指定用户已发布博客")
async def get_user_blog(rid: int, db: db_dependency):
    try:
        user_blog = await query_user_blogs(rid, BlogStateEnum.publish, db)
        if user_blog is None:
            raise HTTPException(404, "获取博客失败")
        return {"msg": "获取成功", "blogs": user_blog}
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(404, "获取博客失败")


@blogRouter.post("/user/{rid}/cursor", summary="获取指定用户已发布博客（游标分页）")
async def get_user_blog_cursor(rid: int, body: CursorPageInput, db: db_dependency):
    try:
        page = await query_user_blogs_cursor(
            rid=rid,
            state_=BlogStateEnum.publish,
            cursor=body.cursor,
            limit=body.limit,
            db=db,
        )
        if page is None:
            raise HTTPException(404, "获取博客失败")
        return page
    except Exception as e:
        print(e)
        raise HTTPException(404, "获取博客失败")


@blogRouter.post("/my-draft/cursor", summary="获取当前用户所有草稿（游标分页）")
async def get_my_draft(phone: auth_phone, body: CursorPageInput, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        rid = await query_user_rid(phone, db)
        if rid is None:
            raise HTTPException(404, "用户不存在")

        page = await query_user_blogs_cursor(
            rid=rid,
            state_=BlogStateEnum.draft,
            cursor=body.cursor,
            limit=body.limit,
            db=db
        )
        if page is None:
            raise HTTPException(404, "获取博客失败")
        return page
    except Exception as e:
        print(e)
        raise HTTPException(404, "获取草稿失败")


@blogRouter.get("/dailyblog", summary="每日推荐")
async def get_daily_blog(db: db_dependency):
    return await query_daily_blog(db)


@blogRouter.get("/hot", summary="热门推荐（按点赞数排序）")
async def get_hot_blog(db: db_dependency, m_limit: int):
    rows = await query_hot_blog_by_likes(m_limit, db)
    if rows is None:
        raise HTTPException(404, "获取热门博客失败")
    return {"msg": "获取成功", "blogs": rows}


@blogRouter.post("/hot/cursor", summary="全站热门内容（游标分页）")
async def get_hot_blog_cursor_page(body: CursorPageInput, db: db_dependency):
    page = await query_hot_blog_cursor(cursor=body.cursor, limit=body.limit, db=db)
    if page is None:
        raise HTTPException(404, "获取热门博客失败")
    return page


# 读取有效博客不需要鉴权
@blogRouter.get("/{id}", summary="根据id获取博客")
async def get_blog_by_id(id: int, db: db_dependency):
    return await get_blog(id, 'publish', db)


# 需要鉴权，因为草稿可能包含敏感信息，且只能由作者本人访问
@blogRouter.get("/draft/{id}", summary="根据id获取草稿")
async def get_draft_by_id(id: int, db: db_dependency, phone: auth_phone):
    # 根据id获取草稿,需要鉴权，且只能由作者本人访问
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    return await get_blog(id, 'publish', db, phone)


# 创建博客
@blogRouter.post("/my-blog/new", summary="创建博客")
@limiter.limit("15/month")
async def upload_blog(request: Request, data: BlogData, db: db_dependency, phone: auth_phone):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        rid = await query_user_rid(phone, db)
        author_name = (
            await db.execute(select(User.username).where(User.reks_id == rid))).scalar_one_or_none()
        # XSS清洗 插入数据库
        data.content = await clean_content(data.content)
        is_insert = await upsert_blog(data, rid, 0, 1, db)
        if is_insert is True:
            await publish_event_to_followers(
                author_id=rid,
                event_type="following.blog.published",
                payload={
                    "authorId": rid,
                    "authorName": author_name or f"用户{rid}",
                    "title": data.title,
                    "kind": "blog",
                },
            )
            return {"msg": is_insert}
        else:
            raise HTTPException(405, "创建失败1")
    except Exception as e:
        print(e)
        raise HTTPException(405, "创建失败2")


@blogRouter.post("/my-blog/new-mblog", summary="创建音乐博客")
@limiter.limit("15/month")
async def upload_mblog(request: Request, data: BlogData, db: db_dependency, phone: auth_phone):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    if data.music_id == 0:
        raise HTTPException(404, "未上传正确的id")
    print(data.music_id)
    try:
        rid = await query_user_rid(phone, db)
        author_name = (
            await db.execute(select(User.username).where(User.reks_id == rid))).scalar_one_or_none()
        # XSS清洗 插入数据库
        data.content = await clean_content(data.content)
        # 调用 music 服务创建音乐博客（内部会创建 blog 并关联 music
        ok = await create_music_blog(data, rid, data.music_id, db)
        if ok:
            await publish_event_to_followers(
                author_id=rid,
                event_type="following.music_blog.published",
                payload={
                    "authorId": rid,
                    "authorName": author_name or f"用户{rid}",
                    "title": data.title,
                    "kind": "music-blog",
                    "musicId": data.music_id,
                },
            )
            return {"msg": True}
        else:
            raise HTTPException(400, "创建音乐博客失败")
    except Exception as e:
        print(e)
        raise HTTPException(400, "创建音乐博客失败")


@blogRouter.post("/my-draft/new", summary="创建草稿")
@limiter.limit("30/month")
async def upload_draft(request: Request, data: BlogData, db: db_dependency, phone: auth_phone):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        rid = await query_user_rid(phone, db)
        # XSS清洗 插入数据库
        data.content = await clean_content(data.content)
        is_insert = await upsert_blog(data, rid, 0, 1, db, 0)
        if is_insert is True:
            return {"msg": is_insert}
        else:
            raise HTTPException(405, "创建失败1")
    except Exception as e:
        print(e)
        raise HTTPException(405, "创建失败2")


@blogRouter.post("/my-blog/update", summary="更新博客")
async def update_blog(request: Request, data: BlogData, blog_id: int, db: db_dependency,
                      phone: auth_phone):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        rid = await query_user_rid(phone, db)
        # XSS清洗 插入数据库
        data.content = await clean_content(data.content)
        is_insert = await upsert_blog(data, rid, blog_id, 1, db)
        if is_insert is True:
            return {"msg": is_insert}
        else:
            raise HTTPException(405, "创建失败1")
    except Exception as e:
        print(e)
        raise HTTPException(405, "创建失败2")


@blogRouter.post("/my-draft/update", summary="更新草稿")
async def update_draft(request: Request, data: BlogData, blog_id: int, db: db_dependency,
                       phone: auth_phone):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        rid = await query_user_rid(phone, db)
        # XSS清洗 插入数据库
        data.content = await clean_content(data.content)
        is_insert = await upsert_blog(data, rid, blog_id, 0, db)
        if is_insert is True:
            return {"msg": is_insert}
        else:
            raise HTTPException(405, "创建失败1")
    except Exception as e:
        print(e)
        raise HTTPException(405, "创建失败2")


@blogRouter.post("/draft/publish", summary="发布草稿")
async def publish_draft(request: Request, blog_id: int, db: db_dependency,
                        phone: auth_phone):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")

    res = await _publish_draft(blog_id, db, rid)
    if res:
        return rback(200, "发布草稿成功")
    else:
        raise HTTPException(400, "发布草稿失败")


# 通用删除，可以删博客和草稿
@blogRouter.delete("/delete", summary="删除博客")
async def delete_blog(phone: auth_phone, db: db_dependency, blog_id: int):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")

    try:
        isDelete = await soft_delete_blog(db, blog_id, rid)
        if isDelete is True:
            return rback(200, "删除成功")
    except Exception as e:
        print(e)
        raise HTTPException(400, "删除失败")


# 上传图片
@blogRouter.post("/upload/img", summary="上传图片")
async def upload_img(phone: auth_phone, db: db_dependency, img: UploadFile = File(...)):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    if not (img.content_type.startswith("image/")):
        raise HTTPException(400, "文件格式不符合要求")

    # 先解哈希然后找相同哈希
    # bug:先行返回的链接可能与上传后的链接存在时间差异，导致命名差异
    cur_md5 = await file_md5(img)
    existed = await query_by_hash(cur_md5, db)
    if existed:
        print("-----存在")
        return {"errno": 0, "data": {"url": existed, "alt": f"reks-{existed}"}}
    try:
        # 根据手机号获取用户的id
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        rid = await query_user_rid(phone, db)
        href = await pre_img_link(rid, img, timestamp)
        # 先行落库
        await insert_into_gallery(rid, href, cur_md5, db)
        # 后台异步
        # background.add_task(img_upload, rid, img)
        await img_upload(rid, img, timestamp)

        if href is None:
            return {
                "errno": 1,
                "message": HTTPException(400, "上传失败")
            }
        else:
            return {
                "errno": 0,
                "data": {
                    "url": href,
                    "alt": f"reks-{href}"
                }
            }
    except Exception as e:
        print(e)
        raise HTTPException(400, "上传丢失/失败")


@blogRouter.get("/tags/hot", summary="热门标签")
async def get_hot_tags(phone: auth_phone, db: db_dependency):
    # Require valid auth
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")

    try:
        # Count associations between published blogs and tags, order by count desc, limit 10
        stmt = (
            select(Tag.name, func.count(blogs_tags.c.blog_id).label("count"))
            .select_from(blogs_tags)
            .join(Tag, Tag.id == blogs_tags.c.tag_id)
            .join(Blog, Blog.id == blogs_tags.c.blog_id)
            .where(Blog.state == BlogStateEnum.publish)
            .group_by(Tag.id, Tag.name)
            .order_by(func.count(blogs_tags.c.blog_id).desc())
            .limit(10)
        )

        rows = (await db.execute(stmt)).mappings().all()

        tags = [{"name": r["name"], "count": int(r["count"])} for r in rows]

        return {"msg": "获取成功", "tags": tags}
    except Exception as e:
        print(e)
        raise HTTPException(404, "获取热门标签失败")
