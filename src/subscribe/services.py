import json

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as prt

from src.database.pg_connector import SessionLocal
from src.database.redis_train import STREAM_KEY, rd_stm
from src.orm.model import Contact, User
from src.user.services import query_user_rid


async def insert_follow(fid: int, phone: str) -> bool:
    async with (SessionLocal() as db):
        try:
            myid = await query_user_rid(phone, db)
            if myid is None:
                return False
            if myid == fid:
                return False

            target_stmt = select(User.reks_id).where(User.reks_id == fid)
            target_id = (await db.execute(target_stmt)).scalar_one_or_none()
            if target_id is None:
                return False

            stmt = (
                prt(Contact)
                .values(user_id=myid, followed_user_id=fid)
                .on_conflict_do_nothing(
                    index_elements=["user_id", "followed_user_id"],
                )
                .returning(Contact.id)
            )
            await db.execute(stmt)
            await db.commit()

            # 已关注(冲突)和首次关注都视为成功，保持接口幂等
            return True

        except Exception:
            await db.rollback()
            return False


async def remove_follow(fid: int, phone: str) -> bool:
    async with (SessionLocal() as db):
        try:
            myid = await query_user_rid(phone, db)
            if myid is None:
                return False

            stmt = delete(Contact).where(
                Contact.user_id == myid,
                Contact.followed_user_id == fid,
            )
            result = await db.execute(stmt)
            await db.commit()
            return (result.rowcount or 0) > 0
        except Exception:
            await db.rollback()
            return False


async def query_follow_stats(phone: str) -> tuple[int, int] | None:
    async with (SessionLocal() as db):
        myid = await query_user_rid(phone, db)
        if myid is None:
            return None

        following_stmt = select(func.count()).select_from(Contact).where(Contact.user_id == myid)
        follower_stmt = select(func.count()).select_from(Contact).where(Contact.followed_user_id == myid)

        following_count = (await db.execute(following_stmt)).scalar_one() or 0
        follower_count = (await db.execute(follower_stmt)).scalar_one() or 0
        return int(following_count), int(follower_count)


async def query_follow_stats_by_rid(rid: int) -> tuple[int, int]:
    async with (SessionLocal() as db):
        following_stmt = select(func.count()).select_from(Contact).where(Contact.user_id == rid)
        follower_stmt = select(func.count()).select_from(Contact).where(Contact.followed_user_id == rid)

        following_count = (await db.execute(following_stmt)).scalar_one() or 0
        follower_count = (await db.execute(follower_stmt)).scalar_one() or 0
        return int(following_count), int(follower_count)


async def query_following_list(phone: str) -> list[dict]:
    async with (SessionLocal() as db):
        myid = await query_user_rid(phone, db)
        if myid is None:
            return []

        stmt = (
            select(User.reks_id, User.username, User.avatar, User.signature)
            .join(Contact, Contact.followed_user_id == User.reks_id)
            .where(Contact.user_id == myid)
            .order_by(Contact.created_at.desc())
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "rid": row.reks_id,
                "username": row.username,
                "avatar": row.avatar,
                "signature": row.signature,
            }
            for row in rows
        ]


async def query_follower_list(phone: str) -> list[dict]:
    async with (SessionLocal() as db):
        myid = await query_user_rid(phone, db)
        if myid is None:
            return []

        stmt = (
            select(User.reks_id, User.username, User.avatar, User.signature)
            .join(Contact, Contact.user_id == User.reks_id)
            .where(Contact.followed_user_id == myid)
            .order_by(Contact.created_at.desc())
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "rid": row.reks_id,
                "username": row.username,
                "avatar": row.avatar,
                "signature": row.signature,
            }
            for row in rows
        ]


async def publish_event(receiver_id: int, event_type: str, payload: dict | str) -> str | None:
    """写入 Redis Stream 事件。"""
    try:
        payload_text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        return await rd_stm.xadd(
            STREAM_KEY,
            {
                "receiver_id": str(receiver_id),
                "event_type": event_type,
                "data": payload_text,
            },
            maxlen=20000,
            approximate=True,
        )
    except Exception as e:
        print(f"publish_event failed: {e}")
        return None


async def publish_event_to_followers(author_id: int, event_type: str, payload: dict | str) -> int:
    """向 author_id 的全部关注者推送事件，返回推送成功条数。"""
    async with (SessionLocal() as db):
        try:
            stmt = select(Contact.user_id).where(Contact.followed_user_id == author_id)
            follower_ids = (await db.execute(stmt)).scalars().all()

            success = 0
            for follower_id in follower_ids:
                msg_id = await publish_event(int(follower_id), event_type, payload)
                if msg_id is not None:
                    success += 1
            return success
        except Exception as e:
            print(f"publish_event_to_followers failed: {e}")
            return 0