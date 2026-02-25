import asyncio
import json

from src.database.redis_connector import get_redis
from src.database.redis_train import rd_stm, STREAM_KEY

RCODE = "uu_PBvXUhH5CLhsanDE1TmlqBrF0jkh8pZxjl461bPw"

# 类型：推送数据
# 适用于测试 消息推送
# 向对应的rcode投送一条新信息
async def main() -> None:
    rd = get_redis()
    try:
        receiver = await rd.get(f"sess:{RCODE}")
        print("receiver=", receiver)
        if not receiver:
            print("rcode未命中，请更新RCODE后重试")
            return

        payload = {
            "blogId": 10086,
            "title": "实时联调测试：这是一条新的订阅消息",
            "authorId": 9527,
        }

        stream_id = await rd_stm.xadd(
            STREAM_KEY,
            {
                "receiver_id": str(receiver),
                "data": json.dumps(payload, ensure_ascii=False),
            },
        )
        print("xadd success:", stream_id)
    finally:
        await rd.aclose()
        await rd_stm.aclose()
        await rd.connection_pool.disconnect()
        await rd_stm.connection_pool.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
