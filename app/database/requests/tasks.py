import asyncio
import logging

from sqlalchemy import select, func

from app.database.db import async_session
from app.database.models import (
    ProxyRental, ProxyServer, Proxy, ProxyPorts,
    Protocol, Operator, ProxyType
)
from app.database.requests.save_data import update_proxy_status, update_port_status
from app.database.requests.task_handler import add_task_to_queue, wait_for_task_completion
from config import CHECK_INTERVAL_SECONDS


async def clean_expired_proxy_rentals():
    """
    Continuously checks for and processes expired proxy rentals.

    This function runs in an infinite loop. It:
        - Selects all proxy rentals with an `expire_date` less than or equal to the current time.
        - For each expired rental:
            - Gathers associated proxy, port, protocol, and operator data.
            - Adds a task to the queue to remove the proxy configuration from the server.
            - Waits briefly for the task to complete.
            - Marks the proxy and port as "Available".
            - Deletes the expired rental from the database.
        - If errors occur, logs the issue and still attempts to clean up and remove the expired rental.

    This function sleeps between cycles based on the configured interval.

    Raises:
        Exception: Any unhandled exception during database operations or task management
                  will be logged and retried.
    """
    while True:
        async with async_session() as session:
            expired_rentals = (await session.execute(
                select(ProxyRental).where(ProxyRental.expire_date <= func.now()))
            ).scalars().all()

        for rental in expired_rentals:
            task_id = None
            try:
                async with async_session() as session:
                    async with session.begin():
                        result = await session.execute(
                            select(
                                ProxyServer.ip.label("server_ip"),
                                Proxy.internal_ip,
                                ProxyPorts.port,
                                Protocol.value.label("protocol"),
                                Operator.name.label("operator")
                            ).join(Proxy, ProxyServer.id == Proxy.server_id)
                            .join(ProxyType, ProxyType.id == Proxy.proxy_type_id)
                            .join(Protocol, Protocol.id == ProxyType.protocol_id)
                            .join(Operator, Operator.id == ProxyType.operator_id)
                            .join(ProxyPorts, ProxyPorts.id == rental.port_id)
                            .where(Proxy.id == rental.proxy_id)
                        )
                        data = result.first()
                        if not data:
                            logging.warning(f"⚠️ No data found for rental_id={rental.id}. Skipping.")
                            continue

                        task_id = await add_task_to_queue(
                            proxy_id=rental.proxy_id,
                            port_id=rental.port_id,
                            login=rental.login,
                            password=rental.password,
                            task_type="remove_proxy"
                        )

                # Wait for task completion (outside transaction)
                success = await wait_for_task_completion(task_id, timeout=5)
                if not success:
                    logging.warning(f"⏳ Timeout while waiting for remove_proxy task for rental_id={rental.id}")

                # Update statuses and delete rental
                async with async_session() as session:
                    async with session.begin():
                        await update_proxy_status(rental.proxy_id, status="Available")
                        await update_port_status(rental.port_id, status="Available")
                        await session.delete(rental)

                logging.info(f"✅ Rental rental_id={rental.id} successfully cleaned up")

            except Exception as e:
                rental_id = getattr(rental, "id", "unknown")

                # Attempt to delete the rental even if task failed
                try:
                    async with async_session() as session:
                        async with session.begin():
                            await update_proxy_status(rental.proxy_id, status="Available")
                            await update_port_status(rental.port_id, status="Available")
                            await session.delete(rental)
                    logging.warning(f"⚠️ Rental rental_id={rental_id} forcibly removed after error")
                except Exception as ex:
                    logging.error(f"❌ Secondary error while removing rental_id={rental_id}: {ex}")

                logging.error(f"❌ Error while cleaning up rental_id={rental_id}: {e}")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
