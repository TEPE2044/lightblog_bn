# python
# 文件：`test/test_connect_pg.py`
import asyncpg

from src.config import settings

connection = None
try:
    connection = asyncpg.connect(
        database="reksblog",
        user="pgadmin",
        password=settings.pgdb_password,
        host="113.46.155.82",
        port="5432"
    )
    print("Connection successful")
except Exception as e:
    print("Connection failed:", e)
finally:
    if connection:
        connection.close()
