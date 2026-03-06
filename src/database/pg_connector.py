# 数据库相关
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config import settings

engine = create_async_engine(settings.pgdb_url, echo=False, pool_pre_ping=True, pool_recycle=3600, pool_size=2,
                             max_overflow=5)  # echo=True 打印SQL日志
# SessionLocal 会话工厂，创建会话
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession, autocommit=False,
                                  autoflush=False)


# -> 返回类型注释，标识函数“返回”的是什么类型的值
# yield（在同步/异步生成器里）是把一个值“产出”并暂停函数状态，控制权回到调用者，之后可恢复继续执行。
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
