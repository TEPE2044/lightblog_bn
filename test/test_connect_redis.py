import asyncio
from src.auth.services import recent
from src.database import get_redis_conn  # 异步生成器


async def main():
    async with get_redis_conn() as rd:
        ok = await recent("18998032090", rd)
        return ok


if __name__ == "__main__":
    asyncio.run(main())
