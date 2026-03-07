from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Request

from src.blog.schemas import BlogData
from src.blog.services import get_blogs, upsert_blog, query_user_blogs, insert_into_gallery, \
    file_md5, query_by_hash, query_daily_blog
from src.database import db_dependency
from src.deps import limiter
from src.orm import BlogStateEnum
from src.user.services import auth_phone, query_user_rid
from src.utils.obs_client import img_upload, pre_img_link
from src.utils.xss_clean import clean_content
from src.music.services import create_music_blog

blogRouter = APIRouter(prefix="/blog", tags=["博客模块"])


# 博客CRUD

# bug-fix:根目录下首先注册blog/{id}后，任何这个格式都会被要求提供参数
# TODO:分页查询
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


@blogRouter.get("/my-draft", summary="获取当前用户所有草稿")
async def get_my_draft(phone: auth_phone, db: db_dependency):
    pass


@blogRouter.get("/dailyblog", summary="每日推荐")
async def get_daily_blog(db: db_dependency):
    return await query_daily_blog(db)


# 读取有效博客不需要鉴权
@blogRouter.get("/{id}", summary="根据id获取博客")
async def get_blog_by_id(id: int, db: db_dependency):
    return await get_blogs(id, db)


# 需要鉴权，因为草稿可能包含敏感信息，且只能由作者本人访问
@blogRouter.get("/draft/{id}", summary="根据id获取草稿")
async def get_draft_by_id(id: int, db: db_dependency, phone: auth_phone):
    # TODO:根据id获取草稿,需要鉴权，且只能由作者本人访问
    pass


# 创建博客
@blogRouter.post("/my-blog/new", summary="创建博客")
@limiter.limit("15/month")
async def upload_blog(request: Request, data: BlogData, db: db_dependency, phone: auth_phone):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        rid = await query_user_rid(phone, db)
        # XSS清洗 插入数据库
        data.content = await clean_content(data.content)
        is_insert = await upsert_blog(data, rid, 0, 1, db)
        if is_insert is True:
            return {"msg": is_insert}
        else:
            raise HTTPException(405, "创建失败1")
    except Exception as e:
        print(e)
        raise HTTPException(405, "创建失败2")


@blogRouter.post("/my-blog/new-mblog")
@limiter.limit("15/month")
async def upload_mblog(request: Request, data: BlogData, db: db_dependency, phone: auth_phone):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    if data.music_id == 0:
        raise HTTPException(404,"未上传正确的id")
    print(data.music_id)
    try:
        rid = await query_user_rid(phone, db)
        # XSS清洗 插入数据库
        data.content = await clean_content(data.content)
        # 调用 music 服务创建音乐博客（内部会创建 blog 并关联 music
        ok = await create_music_blog(data, rid, data.music_id, db)
        if ok:
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
        is_insert = await upsert_blog(data, rid, 0, 0, db)
        if is_insert is True:
            return {"msg": is_insert}
        else:
            raise HTTPException(405, "创建失败1")
    except Exception as e:
        print(e)
        raise HTTPException(405, "创建失败2")


@blogRouter.post("/my-blog/{id}", summary="更新博客")
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


@blogRouter.post("/my-draft/{id}", summary="更新草稿")
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


@blogRouter.post("/publish/{id}", summary="发布草稿")
async def publish_draft(request: Request, blog_id: int, db: db_dependency,
                        phone: auth_phone):
    # TODO:发布草稿,只需要将type改为1即可
    pass


# TODO:删除博客
@blogRouter.delete("/delete-blog", summary="删除博客")
async def delete_blog(phone: auth_phone, db: db_dependency):
    pass


@blogRouter.delete("/delete-draft", summary="删除草稿")
async def delete_draft(phone: auth_phone, db: db_dependency):
    pass


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
