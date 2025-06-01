from sqlite3 import IntegrityError
from sqlalchemy import select
from app.database.db import async_session
from app.database.models import Protocol, Status


async def insert_default_protocols():
    """Insert default protocols into the database if they are not already present.

    This function checks if "SOCKS5" and "HTTP" protocols exist in the `Protocol` table.
    If not, it inserts them. Commits changes unless an IntegrityError occurs, in which case
    it rolls back the transaction.

    Raises:
        IntegrityError: If database constraints are violated during insert.
    """
    async with async_session() as session:
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
    """Insert default statuses into the database if they are not already present.

    This function checks for status entries with IDs 1, 2, and 3 and their respective values
    ("Available", "Rented", "Unavailable"). If any are missing, it inserts them.
    Commits changes unless an IntegrityError occurs, in which case it rolls back.

    Raises:
        IntegrityError: If database constraints are violated during insert.
    """
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
