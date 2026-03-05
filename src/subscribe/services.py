from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as prt

from src.database.pg_connector import SessionLocal
from src.orm.model import Contact, User


async def insert_follow(fid: int, phone: str) -> bool:
    async with (SessionLocal() as db):
        try:
            my_stmt = select(User.reks_id).where(User.phone == phone)
            myid = (await db.execute(my_stmt)).scalar_one_or_none()
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
            my_stmt = select(User.reks_id).where(User.phone == phone)
            myid = (await db.execute(my_stmt)).scalar_one_or_none()
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