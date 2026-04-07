from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import fastapi_cdn_host
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware

from src import custom_openapi
from src.auth.router import authRouter
from src.blog.router import blogRouter
from src.deps import limiter
from src.fav.router import favRouter
from src.notification.resolvers import notifRouter
from src.search.resolvers import searchRouter

from src.subscribe.resolvers import subscribeRouter
from src.user.router import userRouter
from src.music.router import musicRouter

app = FastAPI(title='reksblog', openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs", redoc_url="/api/v1/redoc",
              version="0.5.0")

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:9022"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    raise HTTPException(
        status_code=429,
        detail={"msg": "请求已超过限制次数"}
    )


fastapi_cdn_host.patch_docs(app)
# API Version 1.0.0

v1 = APIRouter(prefix="/api/v1")
v1.include_router(userRouter)
v1.include_router(subscribeRouter, tags=['订阅模块'])
v1.include_router(searchRouter, tags=['搜索模块'])
v1.include_router(notifRouter, tags=['公告模块'])
v1.include_router(authRouter)
v1.include_router(blogRouter)
v1.include_router(musicRouter)
v1.include_router(favRouter)
app.include_router(v1)
app.openapi = custom_openapi(app)


# MainRouter
@app.get("/", tags=["根路由"])
async def root():
    return {"message": "ReKindlers-音乐轻博客平台"}
