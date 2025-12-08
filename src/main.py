from fastapi import FastAPI, APIRouter
import fastapi_cdn_host
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import authRouter

app = FastAPI(title='reksblog', openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs",
              redoc_url="/api/v1/redoc", )
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
app.include_router(v1)


# MainRouter
@app.get("/", tags=["根路由"])
async def root():
    return {"message": "ReKindlers-音乐轻博客平台"}
