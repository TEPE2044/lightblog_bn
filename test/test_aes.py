import asyncio

from src.utils.aes_client import decrypt_phone

# 解密aes
phone = '-pM47VOEIbtcbgFZpjXL02wfO-ZiYTKycHIA5izukxihjM_WVdsk'


async def test_decrypt_phone(phone: str) -> str:
    phone = await decrypt_phone(phone)
    print(phone)
    return phone

asyncio.run(test_decrypt_phone(phone))
