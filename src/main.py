from fastapi import FastAPI
import fastapi_cdn_host
from src.auth.router import authRouter

app = FastAPI()

fastapi_cdn_host.patch_docs(app)

# MainRouter
@app.get("/")
async def root():
    return {"message": "ReKindlers-音乐轻博客平台"}

app.include_router(authRouter, prefix="/auth")