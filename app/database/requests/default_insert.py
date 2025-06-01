from sqlite3 import IntegrityError

from sqlalchemy import select

from app.database.db import async_session
from app.database.models import Protocol, Status


async def insert_default_protocols():
    async with async_session() as session:
        # Перевіримо, чи вже існують потрібні записи, щоб уникнути дублювання
        result = await session.execute(select(Protocol).where(Protocol.value.in_(["SOCKS5", "HTTP"])))
        existing = result.scalars().all()

        existing_values = {p.value for p in existing}
        new_protocols = []

        if "SOCKS5" not in existing_values:
            new_protocols.append(Protocol(value="SOCKS5"))
        if "HTTP" not in existing_values:
            new_protocols.append(Protocol(value="HTTP"))
        if new_protocols:
            session.add_all(new_protocols)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise


async def insert_default_statuses():
    async with async_session() as session:
        result = await session.execute(select(Status))
        existing_statuses = result.scalars().all()

        existing_ids = {status.id for status in existing_statuses}

        new_statuses = []

        if 1 not in existing_ids:
            new_statuses.append(Status(id=1, value="Available"))
        if 2 not in existing_ids:
            new_statuses.append(Status(id=2, value="Rented"))
        if 3 not in existing_ids:
            new_statuses.append(Status(id=3, value="Unavailable"))

        if new_statuses:
            session.add_all(new_statuses)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise

