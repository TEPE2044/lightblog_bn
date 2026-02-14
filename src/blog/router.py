from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Request

from src.blog.schemas import BlogData
from src.blog.services import get_blogs, upsert_blog, query_user_blogs, insert_into_gallery, \
    file_md5, query_by_hash
from src.database import db_dependency
from src.deps import limiter
from src.user.services import auth_phone, query_user_rid
from src.utils.obs_client import img_upload, pre_link
from src.utils.xss_clean import clean_content

blogRouter = APIRouter(prefix="/blog", tags=["博客模块"])


# 博客CRUD

# bug-fix:根目录下首先注册blog/{id}后，任何这个格式都会被要求提供参数
# TODO:分页查询
@blogRouter.get("/my-blog", summary="获取当前用户所有博客和草稿")
async def get_my_blog(phone: auth_phone, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        rid = await query_user_rid(phone, db)
        if rid is None:
            raise HTTPException(404, "用户不存在")
        my_blog = await query_user_blogs(rid, db)
        if my_blog is not None:
            return {"msg": "获取成功", "blogs": my_blog}
    except Exception as e:
        print(e)
        raise HTTPException(404, "获取博客失败")


# 读取有效博客不需要鉴权
@blogRouter.get("/{id}", summary="根据id获取博客")
async def get_blog_by_id(id: int, db: db_dependency):
    return await get_blogs(id, db)


# 使用PostgreSQL的upsert方法，插入与更新一体化
# 关联一个user_id
@blogRouter.post("/my-blog/new", summary="创建博客")
@limiter.limit("15/month")
async def upload_blog(request: Request, data: BlogData, db: db_dependency, phone: auth_phone,
                      blog_id: Optional[int] = 0):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        rid = await query_user_rid(phone, db)
        # XSS清洗 插入数据库
        data.content = await clean_content(data.content)
        is_insert = await upsert_blog(data, rid, blog_id or 0, db)
        if is_insert is True:
            return {"msg": is_insert}
        else:
            raise HTTPException(405, "创建失败1")
    except Exception as e:
        print(e)
        raise HTTPException(405, "创建失败2")


@blogRouter.delete("/delete-blog", summary="删除博客")
async def delete_blog(phone: auth_phone, db: db_dependency, id: int):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")


# 异步上传
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
        href = await pre_link(rid, img, timestamp)
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
