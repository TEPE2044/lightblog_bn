from fastapi import FastAPI, APIRouter
import fastapi_cdn_host
from starlette.middleware.cors import CORSMiddleware

from src import custom_openapi
from src.auth.router import authRouter
from src.gql.router import gql_router
from src.user.router import userRouter

app = FastAPI(title='reksblog', openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs", redoc_url="/api/v1/redoc",
              version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
fastapi_cdn_host.patch_docs(app)
# API Version 1.0.0
v1 = APIRouter(prefix="/api/v1")
v1.include_router(authRouter)
v1.include_router(userRouter)
v1.include_router(gql_router)
app.include_router(v1)
app.openapi = custom_openapi(app)


# MainRouter
@app.get("/", tags=["根路由"])
async def root():
    return {"message": "ReKindlers-音乐轻博客平台"}

