import asyncio
import json

from src.database.redis_connector import get_redis
from src.database.redis_train import rd_stm, STREAM_KEY

RCODE = "uu_PBvXUhH5CLhsanDE1TmlqBrF0jkh8pZxjl461bPw"


async def main() -> None:
    rd = get_redis()
    try:
        phone = await rd.get(f"sess:{RCODE}")
        print("receiver(phone)=", phone)
        if not phone:
            print("rcode在rd_local中不存在，请先登录或刷新token")
            return

        payload = {
            "blogId": 9527,
            "title": "订阅联调测试：你现在能收到这条了",
            "authorId": 10001,
        }
        event_id = await rd_stm.xadd(
            STREAM_KEY,
            {
                "receiver_id": str(phone),
                "data": json.dumps(payload, ensure_ascii=False),
            },
        )
        print("xadd success, stream_id=", event_id)
    finally:
        await rd.close()


if __name__ == "__main__":
    asyncio.run(main())
