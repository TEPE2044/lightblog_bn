import asyncio

from src.utils.jwt_client import create_access_token


async def test_create_access_token():
    card = await create_access_token("18998032090")
    print(card)


asyncio.run(test_create_access_token())