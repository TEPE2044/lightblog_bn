from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.dialects.postgresql import insert

from src.database import db_dependency
from src.music.schemas import AudioBase
from src.music.services import audio_upload, insert_into_music
from src.orm.model import Music
from src.user.services import auth_phone, query_user_rid
from src.utils.obs_client import pre_audio_link

musicRouter = APIRouter(prefix='/music', tags=['音乐模块'])


@musicRouter.post("/my-music/new", summary="上传音乐")
async def upload_new_music(phone: auth_phone, db: db_dependency, data: AudioBase):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    try:
        if data is None:
            raise HTTPException(422, "上传类型错误")
        rid = await query_user_rid(phone, db)
        if rid is None:
            raise HTTPException(404, "用户不存在")
        print("----1")
        is_insert = await insert_into_music(data, db, rid)
        if is_insert is False:
            raise HTTPException(500, "音频上传失败")
        return {"status": 200, "msg": is_insert}
    except Exception as e:
        print(e)
        raise HTTPException(500, "音频上传失败")


# 上传音频接口：1.返回预链接入库 2.后台上传
# TODO:3.GraphQL订阅在完成时负责通知 4.音频去重
@musicRouter.post("/upload/audio", summary="上传音频")
async def upload_audio(phone: auth_phone, db: db_dependency, background: BackgroundTasks,
                       audio: UploadFile = File(...)):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    if not (audio.content_type.startswith("audio/")):
        raise HTTPException(400, "文件格式不符合要求")

    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        rid = await query_user_rid(phone, db)
        href = await pre_audio_link(rid, audio, timestamp)
        # 后台上传
        background.add_task(audio_upload, rid, audio, timestamp)
        return {"status": 200, "msg": "上传成功", "link": href}
    except Exception as e:
        print(e)
        raise HTTPException(500, "上传失败")
