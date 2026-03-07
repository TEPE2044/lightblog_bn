import asyncio
import json
import uuid
from typing import AsyncIterator

import strawberry
from strawberry import Info
from strawberry.fastapi import GraphQLRouter

from src.database.redis_connector import get_redis
from src.database.redis_train import GROUP_NAME, STREAM_KEY, ensure_group, rd_stm
from src.gql import HTTPResult
from src.gql.deps import auth_current_user, _collect_headers
from src.subscribe import EventSnapshot, FollowStatsSnapshot, FollowUserSnapshot
from src.subscribe.services import (
    insert_follow,
    query_follower_list,
    query_follow_stats,
    query_follow_stats_by_rid,
    query_following_list,
    remove_follow,
)


@strawberry.type
class Query:
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

    @strawberry.field
    async def follow_stats_by_rid(self, rid: int) -> FollowStatsSnapshot:
        following_count, follower_count = await query_follow_stats_by_rid(rid)
        return FollowStatsSnapshot(
            followingCount=following_count,
            followerCount=follower_count,
        )


@strawberry.type
class Mutation:
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
    @strawberry.subscription
    async def push_event(self, info: Info) -> AsyncIterator[EventSnapshot]:
        # headers = _collect_headers(info)
        # rd = get_redis()
        # AsyncIterator 意思是 这个函数不是一次返回一个值，而是异步地持续产出多个BlogSnapshot
        phone = await auth_current_user(_collect_headers(info), get_redis())
        if not phone:
            raise Exception("UNAUTHORIZED")

        # 确认存在消息流
        await ensure_group()
        # 为坠落的人类命名（
        consumer_name = f"sub-{uuid.uuid4().hex}"
        # 订阅场景的长循环
        try:
            while True:
                entries = await rd_stm.xreadgroup(
                    groupname=GROUP_NAME,
                    consumername=consumer_name,
                    streams={STREAM_KEY: ">"},
                    count=10,
                    block=5000,
                )

                if not entries:
                    continue

                for _, messages in entries:
                    for msg_id, fields in messages:
                        receiver_id = str(fields.get("receiver_id") or "")
                        if receiver_id != str(phone):
                            await rd_stm.xack(STREAM_KEY, GROUP_NAME, msg_id)
                            continue

                        event_type = str(fields.get("event_type") or "blog.published")
                        payload = fields.get("data") or "{}"

                        if not isinstance(payload, str):
                            payload = json.dumps(payload, ensure_ascii=False)

                        await rd_stm.xack(STREAM_KEY, GROUP_NAME, msg_id)
                        yield EventSnapshot(eventType=event_type, payload=payload)
                        # yield：产出一个值并“暂停”，下次还能从暂停点继续执行。
        except asyncio.CancelledError as e:
            raise e


subscribe = strawberry.Schema(subscription=Subscription, query=Query, mutation=Mutation)
subscribeRouter = GraphQLRouter(subscribe, path="/gql/subql")
