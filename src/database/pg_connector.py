# 数据库相关
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config import settings
from sqlalchemy.pool import NullPool

import os
# engine:该对象充当连接到特定数据库的中心来源，同时提供工厂以及称为连接池的存储空间来管理这些数据库连接。引擎通常是一个全局对象，为特定的数据库服务器仅创建一次，并使用描述其如何连接到数据库主机或后端的 URL 字符串进行配置。

APP_ENV = str(os.environ.get('APP_ENV'))
if APP_ENV == 'prod':
    # SERVER
    engine = create_async_engine(settings.pgdb_url, echo=False, pool_pre_ping=True, pool_recycle=3600, pool_size=2,
                             max_overflow=5)  # echo=True 打印SQL日志
    print("连接正式环境数据库")
else:
    # SUPABASE
    engine = create_async_engine(
        settings.pgdb_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "statement_cache_size": 0,  # ← 新增：禁用 asyncpg prepared statement 缓存
        },
        poolclass=NullPool,  # ← 新增：禁用 SQLAlchemy 连接池，让 PgBouncer 或 asyncpg 自己管
    )

# SessionLocal 会话工厂，创建会话
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession, autocommit=False,
                                  autoflush=False)


# -> 返回类型注释，标识函数“返回”的是什么类型的值
# yield（在同步/异步生成器里）是把一个值“产出”并暂停函数状态，控制权回到调用者，之后可恢复继续执行。
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
