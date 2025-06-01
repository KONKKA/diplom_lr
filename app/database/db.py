
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from config import DB_URL_PG

engine = create_async_engine(url = DB_URL_PG, echo=True,pool_size=8)

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

async def async_main():
    """
    Create all database tables defined on Base metadata asynchronously.

    This function opens an asynchronous connection to the database
    and creates tables according to the ORM models defined.

    Usage:
        await async_main()
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)