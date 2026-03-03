from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as prt

from src.database import db_dependency
from src.music.schemas import AudioBase
from src.orm.model import Music, User, Blog_Music
from src.utils.obs_client import myBucket, myObs
from src.blog.schemas import BlogData
from src.blog.services import create_or_update_blog_core


async def get_music(rid: int, db: db_dependency) -> list[dict]:
    stmt = (
        select(Music, User.username, User.avatar)
        .join(User, Music.rid == User.reks_id)
        .where(Music.rid == rid)
    )
    result = await db.execute(stmt)
    rows = result.mappings().all()

    return [
        {
            # 自动提取 Music 所有字段（排除 SQLAlchemy 内部属性）
            **{k: v for k, v in row[Music].__dict__.items() if not k.startswith('_')},
            "username": row["username"],
            "avatar": row["avatar"]
        }
        for row in rows
    ]


async def audio_upload(rid: int, audio: UploadFile, timestamp) -> str | None:
    audio_key = f"RAudio/{rid}/{timestamp}_audio{Path(audio.filename).suffix}"
    print("---------")
    print(audio_key)

    try:
        iurl = f"https://{myBucket}.obs.cn-south-1.myhuaweicloud.com/{audio_key}"
        print("---------1")
        myObs.client.putContent(bucketName=myBucket, objectKey=audio_key,
                                content=await audio.read())
        print("---------2")
        return iurl

    except Exception as e:
        print(e)
        try:
            myObs.client.deleteObject(bucketName=myBucket, objectKey=audio_key)
        except Exception as e:
            print(e)
            return None
        return None


async def insert_into_music(data: AudioBase, db: db_dependency, rid: int) -> bool | dict:
    stmt = insert(Music).values(
        name=data.name,
        rid=rid,
        original=data.isOriginal,
        cover=data.coverURL,
        desc=data.desc,
        audio=data.audioURL,
        state=0
    ).returning(Music.id)
    try:
        res = await db.execute(stmt)
        new_id = res.scalar_one_or_none()
        await db.commit()
        return {"is_insert": True, "id": new_id}
    except Exception as e:
        print(e)
        await db.rollback()
        return False


async def create_music_blog(data: BlogData, rid: int, music_id: int, db: db_dependency) -> bool:
    """创建音乐博客：先创建博客（不提交），再插入 blogs_music 关联，最后提交事务。
    返回 True/False
    """
    try:
        # 创建或更新 blog（不提交）
        blog_id = await create_or_update_blog_core(data, rid, 0, 0, db)

        # 确认 music 存在
        row = (await db.execute(select(Music.id).where(Music.id == music_id))).scalar_one_or_none()
        if row is None:
            await db.rollback()
            return False

        # 插入关联表，避免重复使用 on_conflict_do_nothing
        stmt = prt(Blog_Music).values(blog_id=blog_id, music_id=music_id).on_conflict_do_nothing()
        await db.execute(stmt)

        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        print(e)
        return False
