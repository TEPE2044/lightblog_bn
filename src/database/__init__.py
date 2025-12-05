from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from src.database.pg_connector import get_db

Base = declarative_base()

db_dependency = Annotated[AsyncSession, Depends(get_db)]
# usage of Annotated written by JackyView not AI CREATED....
# 1.Annotated[Type, Metadata],example: x = Annotated[int, "This is an integer"]
# 2.tell interpreter than "x" is of type int, with additional metadata
