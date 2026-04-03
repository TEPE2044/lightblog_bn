from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.database import db_dependency
from src.music.schemas import AudioBase, CursorPageInput
from src.music.services import audio_upload, insert_into_music, get_music, get_music_cursor, soft_delete_music
from src.orm.model import Music, User
from src.subscribe.services import publish_event_to_followers
from src.user.services import auth_phone, query_user_rid
from src.utils.Rback import rback

from src.utils.obs_client import pre_audio_link

musicRouter = APIRouter(prefix='/music', tags=['音乐模块'])


@musicRouter.get("/my-music", summary="获取音乐")
async def get_my_music(phone: auth_phone, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    rid = await query_user_rid(phone, db)
    return await get_music(rid, db)


# TODO:音乐应该取消游标分页，结构上不需要
@musicRouter.post("/my-music/cursor", summary="获取当前用户音乐（游标分页）")
async def get_my_music_cursor(phone: auth_phone, body: CursorPageInput, db: db_dependency):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")
    return await get_music_cursor(rid=rid, cursor=body.cursor, limit=body.limit, db=db)


@musicRouter.get("/user/{rid}", summary="获取指定用户音乐")
async def get_user_music(rid: int, db: db_dependency):
    return await get_music(rid, db)


@musicRouter.post("/user/{rid}/cursor", summary="获取指定用户音乐（游标分页）")
async def get_user_music_cursor(rid: int, body: CursorPageInput, db: db_dependency):
    return await get_music_cursor(rid=rid, cursor=body.cursor, limit=body.limit, db=db)


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
        author_name = (await db.execute(select(User.username).where(User.reks_id == rid))).scalar_one_or_none()
        print("----1")
        is_insert = await insert_into_music(data, db, rid)
        if is_insert is False:
            raise HTTPException(500, "音频上传失败")
        if isinstance(is_insert, dict):
            await publish_event_to_followers(
                author_id=rid,
                event_type="following.music.published",
                payload={
                    "authorId": rid,
                    "authorName": author_name or f"用户{rid}",
                    "name": data.name,
                    "kind": "music",
                    "musicId": is_insert.get("id"),
                },
            )
        return {"status": 200, "msg": is_insert}
    except Exception as e:
        print(e)
        raise HTTPException(500, "音频上传失败")


# 上传音频接口：1.返回预链接入库 2.后台上传
# 3.GraphQL订阅在完成时负责通知 TODO:4.音频去重
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


# 软删除
@musicRouter.delete("/delete", summary="删除音乐")
async def delete_music(phone: auth_phone, db: db_dependency, music_id: int):
    if phone is False:
        raise HTTPException(401, "当前登录状态已过期")
    rid = await query_user_rid(phone, db)
    if rid is None:
        raise HTTPException(404, "用户不存在")

    try:
        isDelete = await soft_delete_music(db, music_id, rid)
        print(isDelete)
        if isDelete is True:
            return rback(200, "删除成功")
    except Exception as e:
        print(e)
        raise HTTPException(400, "删除失败")
