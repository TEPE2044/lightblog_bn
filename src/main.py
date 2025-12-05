import http

from fastapi import FastAPI, APIRouter
import fastapi_cdn_host
from src.auth.router import authRouter

app = FastAPI(title='reksblog')

fastapi_cdn_host.patch_docs(app)

root_router = APIRouter(prefix="/api")


# MainRouter
@root_router.get("/", tags=["根路由"])
async def root():
    return {"message": "ReKindlers-音乐轻博客平台"}

root_router.include_router(authRouter,prefix="/auth")

app.include_router(root_router)
