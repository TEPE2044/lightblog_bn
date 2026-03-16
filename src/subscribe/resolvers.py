import asyncio
import json
from typing import AsyncIterator

import strawberry
from strawberry import Info
from strawberry.fastapi import GraphQLRouter

from src.database.redis_connector import get_redis
from src.database.redis_train import STREAM_KEY, rd_stm
from src.database.pg_connector import SessionLocal
from src.gql import HTTPResult
from src.gql.deps import auth_current_user, _collect_headers
from src.subscribe import EventSnapshot, FollowStatsSnapshot, FollowUserSnapshot
from src.user.services import query_user_rid
from src.subscribe.services import (
    insert_follow,
    query_follower_list,
    query_follow_stats,
    query_follow_stats_by_rid,
    query_following_list,
    remove_follow,
)


def _user_stream_cursor_key(rid: int) -> str:
    return f"reksab:subscribe:stream_cursor:{rid}"


@strawberry.type
class Query:
    # 获取用户的关注数量与粉丝数量
    @strawberry.field
    async def follow_stats(self, info: Info) -> FollowStatsSnapshot:
        phone = await auth_current_user(_collect_headers(info), get_redis())
        if not phone:
            raise Exception("UNAUTHORIZED")

        stats = await query_follow_stats(phone)
        if stats is None:
            return FollowStatsSnapshot(followingCount=0, followerCount=0)

        following_count, follower_count = stats
        return FollowStatsSnapshot(
            followingCount=following_count,
            followerCount=follower_count,
        )

    # 获取关注列表
    @strawberry.field
    async def following_list(self, info: Info) -> list[FollowUserSnapshot]:
        phone = await auth_current_user(_collect_headers(info), get_redis())
        if not phone:
            raise Exception("UNAUTHORIZED")

        items = await query_following_list(phone)
        return [
            FollowUserSnapshot(
                rid=item["rid"],
                username=item["username"],
                avatar=item["avatar"],
                signature=item["signature"],
            )
            for item in items
        ]

    # 获取粉丝列表
    @strawberry.field
    async def follower_list(self, info: Info) -> list[FollowUserSnapshot]:
        phone = await auth_current_user(_collect_headers(info), get_redis())
        if not phone:
            raise Exception("UNAUTHORIZED")

        items = await query_follower_list(phone)
        return [
            FollowUserSnapshot(
                rid=item["rid"],
                username=item["username"],
                avatar=item["avatar"],
                signature=item["signature"],
            )
            for item in items
        ]

    # 根据id获取他/她的粉丝列表
    @strawberry.field
    async def follow_stats_by_rid(self, rid: int) -> FollowStatsSnapshot:
        following_count, follower_count = await query_follow_stats_by_rid(rid)
        return FollowStatsSnapshot(
            followingCount=following_count,
            followerCount=follower_count,
        )


@strawberry.type
class Mutation:
    # 关注某人
    @strawberry.mutation
    async def follow(self, info: Info, fid: int) -> HTTPResult:
        phone = await auth_current_user(_collect_headers(info), get_redis())
        if not phone:
            return HTTPResult(status=401, msg="UNAUTHORIZED")
        # TODO:A关注B，建立关系；加入B的频道接收推送
        try:
            is_follow = await insert_follow(fid, phone)
            if is_follow is True:
                return HTTPResult(status=200, msg="关注成功")
            else:
                return HTTPResult(status=403, msg="关注失败，无法关注自己")
        except Exception as e:
            return HTTPResult(status=403, msg=str(e))

    # 取消关注某人
    @strawberry.mutation
    async def unfollow(self, info: Info, fid: int) -> HTTPResult:
        phone = await auth_current_user(_collect_headers(info), get_redis())
        if not phone:
            return HTTPResult(status=401, msg="UNAUTHORIZED")

        try:
            is_removed = await remove_follow(fid, phone)
            if is_removed:
                return HTTPResult(status=200, msg="取消关注成功")
            return HTTPResult(status=404, msg="未找到关注关系")
        except Exception as e:
            return HTTPResult(status=403, msg=str(e))


@strawberry.type
class Subscription:
    # 推送事件
    @strawberry.subscription
    async def push_event(self, info: Info) -> AsyncIterator[EventSnapshot]:
        # headers = _collect_headers(info)
        # rd = get_redis()
        # AsyncIterator 意思是 这个函数不是一次返回一个值，而是异步地持续产出多个BlogSnapshot
        phone = await auth_current_user(_collect_headers(info), get_redis())
        if not phone:
            raise Exception("UNAUTHORIZED")

        async with SessionLocal() as db:
            rid = await query_user_rid(phone, db)
        if rid is None:
            raise Exception("UNAUTHORIZED")

        # 游标与 Stream 放在同一个 Redis（rd_stm）中，避免跨实例导致状态不一致。
        rd = rd_stm
        cursor_key = _user_stream_cursor_key(int(rid))

        # 从 Redis 恢复该用户上次游标；若不存在则从保留窗口起点补读。
        last_id = await rd.get(cursor_key)
        if isinstance(last_id, bytes):
            last_id = last_id.decode("utf-8", errors="ignore")
        if not isinstance(last_id, str) or "-" not in last_id:
            last_id = "0-0"

        # 订阅场景的长循环
        try:
            while True:
                entries = await rd_stm.xread(
                    streams={STREAM_KEY: last_id},
                    count=10,
                    block=5000,
                )

                if not entries:
                    continue

                for _, messages in entries:
                    for msg_id, fields in messages:
                        last_id = msg_id
                        # 持久化游标，保证离线重连后可从断点继续读取。
                        await rd.set(cursor_key, last_id)

                        receiver_id = str(fields.get("receiver_id") or "")
                        if receiver_id != str(rid):
                            continue

                        event_type = str(fields.get("event_type") or "blog.published")
                        payload = fields.get("data") or "{}"

                        if not isinstance(payload, str):
                            payload = json.dumps(payload, ensure_ascii=False)

                        yield EventSnapshot(eventType=event_type, payload=payload)
                        # yield：产出一个值并“暂停”，下次还能从暂停点继续执行。
        except asyncio.CancelledError as e:
            raise e


subscribe = strawberry.Schema(subscription=Subscription, query=Query, mutation=Mutation)
subscribeRouter = GraphQLRouter(subscribe, path="/gql/subql")
