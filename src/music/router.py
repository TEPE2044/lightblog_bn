from fastapi import APIRouter

musicRouter = APIRouter(prefix='/music', tags=['音乐模块'])


@musicRouter.get("/detail/{id}", summary="根据id获取音乐")
async def get_music_by_id():
    pass


@musicRouter.get("/my-music", summary="根据id获取音乐")
async def get_my_tracks():
    pass


@musicRouter.post("/my-music/new",summary="上传音乐")
async def upload_new_music():
    pass
