import asyncio
import logging

from sqlalchemy import select, func
from app.database.db import async_session
from app.database.models import ProxyRental, ProxyServer, Proxy, ProxyPorts, Protocol, Operator, \
    ProxyType
from app.database.requests.save_data import update_proxy_status, update_port_status
from app.database.requests.task_handler import add_task_to_queue, wait_for_task_completion
from config import CHECK_INTERVAL_SECONDS


async def clean_expired_proxy_rentals():
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
                            logging.warning(f"⚠️ Дані для rental_id={rental.id} не знайдено. Пропуск.")
                            continue

                        task_id = await add_task_to_queue(
                            proxy_id=rental.proxy_id,
                            port_id=rental.port_id,
                            login=rental.login,
                            password=rental.password,
                            task_type="remove_proxy"
                        )

                # Очікування завершення задачі (за межами транзакції)
                success = await wait_for_task_completion(task_id, timeout=5)
                if not success:
                    logging.warning(f"⏳ Таймаут remove_proxy для rental_id={rental.id}")

                # Оновлення статусів та видалення оренди
                async with async_session() as session:
                    async with session.begin():
                        await update_proxy_status(rental.proxy_id, status="Available")
                        await update_port_status(rental.port_id, status="Available")
                        await session.delete(rental)

                logging.info(f"✅ Оренда rental_id={rental.id} очищена успішно")

            except Exception as e:
                rental_id = getattr(rental, "id", "невідомо")

                # Все одно видаляємо оренду, якщо не вдалося виконати таску
                try:
                    async with async_session() as session:
                        async with session.begin():
                            await update_proxy_status(rental.proxy_id, status="Available")
                            await update_port_status(rental.port_id, status="Available")
                            await session.delete(rental)
                    logging.warning(f"⚠️ Оренда rental_id={rental_id} була примусово видалена після помилки")
                except Exception as ex:
                    logging.error(f"❌ Повторна помилка при видаленні rental_id={rental_id}: {ex}")

                logging.error(f"❌ Помилка при очищенні rental_id={rental_id}: {e}")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

