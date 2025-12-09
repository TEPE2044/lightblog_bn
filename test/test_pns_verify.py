import asyncio

from src.auth.services import is_code_valid

phoneList = ["18028959280", "1883"]
asyncio.run(is_code_valid(phoneList))

