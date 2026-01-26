from fastapi import APIRouter, HTTPException

from src.blog.schemas import BlogData
from src.blog.services import get_blogs, get_drafts, upsert_blog
from src.database import db_dependency
from src.user.services import auth_phone
from src.utils.xss_clean import clean_content

blogRouter = APIRouter(prefix="/blog", tags=["博客模块"])


# 博客CRUD

# 读取有效博客不需要鉴权
@blogRouter.get("/{rid}", summary="根据rid读取博客")
async def get_blog_by_id(rid: int, db: db_dependency):
    return await get_blogs(rid, db)


@blogRouter.get("/draft/{rid}", summary="根据id读取草稿箱")
async def get_draft(rid: int, db: db_dependency, phone: auth_phone):
    # if phone is False:
    #     raise HTTPException(status_code=401, detail="当前登录状态已过期")
    return await get_drafts(rid, db)


# 使用PostgreSQL的upsert方法，插入与更新一体化
# 关联一个user_id
@blogRouter.post("/upload-blog", summary="创建/修改博客")
async def upload_blog(data: BlogData, db: db_dependency, phone: auth_phone):
    # if phone is False:
    #     raise HTTPException(status_code=401, detail="当前登录状态已过期")
    try:
        # XSS清洗 插入数据库
        data.content = await clean_content(data.content)
        is_insert = await upsert_blog(data, db)
        if is_insert is True:
            return {"msg": is_insert}
        else:
            raise HTTPException(status_code=405, detail="创建/更新失败")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=405, detail="创建/更新失败")


@blogRouter.delete("/delete-blog", summary="删除博客")
async def delete_blog():
    # 返回  204 No Content
    pass
