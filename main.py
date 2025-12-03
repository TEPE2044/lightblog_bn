from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "ReKindlers-音乐轻博客平台"}