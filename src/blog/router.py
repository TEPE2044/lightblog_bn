from fastapi import APIRouter

blogRouter = APIRouter(prefix="/blog", tags=["博客模块"])


# TODO:博客CRUD
@blogRouter.get("/get-blog-by-id", summary="根据id读取博客")
async def get_blog_by_id():
    pass


@blogRouter.post("/upload-blog", summary="创建博客")
async def upload_blog():
    pass


@blogRouter.post("/update-blog", summary="修改博客内容")
async def update_blog():
    pass


@blogRouter.delete("/delete-blog", summary="删除博客")
async def delete_blog():
    # 返回  204 No Content
    pass
