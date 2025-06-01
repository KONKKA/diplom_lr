import logging

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

from app.database.db import async_session
from app.database.models import ProxyCatalog


async def update_proxy_price(catalog_id: int, price: int) -> bool:
    """
    Update the weekly rental price for a specific proxy catalog entry.

    Args:
        catalog_id (int): The ID of the proxy catalog item to update.
        price (int): The new weekly price to be set for the proxy.

    Returns:
        bool: True if the update was successful, False otherwise.

    Raises:
        Logs errors via the logging module instead of raising exceptions directly.
    """
    async with async_session() as session:
        try:
            stmt = (
                update(ProxyCatalog)
                .where(ProxyCatalog.id == catalog_id)
                .values(price_per_week=price)
            )
            await session.execute(stmt)
            await session.commit()
            return True
        except SQLAlchemyError as e:
            logging.error("proxy price update error:", e)
            await session.rollback()
            return False




