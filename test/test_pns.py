# 其实就是sms，别问问就是一样的
import asyncio

from src.auth.services import send_sms_code_async

# 根本就没有用到自己创建的code，那是短信平台生成的
asyncio.run(send_sms_code_async("18028959280", db=None))
