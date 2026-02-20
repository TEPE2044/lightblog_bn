from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import insert, select

from src.database import db_dependency
from src.music.schemas import AudioBase
from src.orm.model import Music, User
from src.utils.obs_client import myBucket, myObs


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
