from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from src.database.pg_connector import get_db
from src.database.redis_connector import get_redis_conn

Base = declarative_base()

db_dependency = Annotated[AsyncSession, Depends(get_db)]
rd_dependency = Annotated[Redis, Depends(get_redis_conn)]
# usage of Annotated written by JackyView not AI CREATED....
# 1.Annotated[Type, Metadata],example: x = Annotated[int, "This is an integer"]
# 2.tell interpreter than "x" is of type int, with additional metadata
