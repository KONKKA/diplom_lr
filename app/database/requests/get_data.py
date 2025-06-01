import logging
from typing import List, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from app.database.db import async_session
from app.database.models import Proxy, Protocol, Operator, Status, ProxyType, ProxyCatalog, User, ProxyServer, \
    ProxyPorts, ProxyRental, ProxyTaskQueue
from app.utils.constants import IPV4_PATTERN


async def get_all_proxies_info() -> List[Dict]:
    async with async_session() as session:
        stmt = (
            select(
                Proxy.id.label("id"),
                ProxyServer.ip.label("server_ip"),
                Proxy.internal_ip.label("internal_ip"),
                Protocol.value.label("protocol"),
                Operator.name.label("operator"),
                Operator.country_code.label("country"),
                Status.value.label("status")
            )
            .select_from(Proxy)
            .join(ProxyServer, Proxy.server_id == ProxyServer.id)
            .join(ProxyType, Proxy.proxy_type_id == ProxyType.id)
            .join(Protocol, ProxyType.protocol_id == Protocol.id)
            .join(Operator, ProxyType.operator_id == Operator.id)
            .join(Status, Proxy.status_id == Status.id)
        )

        result = await session.execute(stmt)
        proxies = result.all()

        return [{
            "id": proxy.id,
            "server_ip": proxy.server_ip,
            "internal_ip": proxy.internal_ip,
            "protocol": proxy.protocol,
            "operator": proxy.operator,
            "country": proxy.country,
            "status": proxy.status
        } for proxy in proxies]


async def get_catalog_item_by_id(proxy_catalog_id: int) -> Optional[dict]:
    async with async_session() as session:
        stmt = (
            select(
                ProxyCatalog.id.label("id"),
                Operator.country_code.label("country_code"),
                Operator.name.label("operator"),
                Protocol.value.label("protocol"),
                ProxyCatalog.available_amount,
                ProxyCatalog.price_per_week,
                ProxyType.id.label("proxy_type_id")
            )
            .select_from(ProxyCatalog)
            .join(ProxyType, ProxyCatalog.proxy_type_id == ProxyType.id)
            .join(Operator, ProxyType.operator_id == Operator.id)
            .join(Protocol, ProxyType.protocol_id == Protocol.id)
            .where(ProxyCatalog.id == proxy_catalog_id)
        )

        result = await session.execute(stmt)
        return result.mappings().first()


async def get_available_catalog():
    await refresh_proxy_catalog()
    async with async_session() as session:
        stmt = (
            select(
                ProxyCatalog.id.label("catalog_id"),
                Protocol.value.label("protocol"),
                Operator.name.label("operator"),
                Operator.country_code.label("country_code"),
                ProxyType.speed.label("speed"),
                ProxyCatalog.available_amount.label("available_amount"),
                ProxyCatalog.price_per_week.label("price_per_week")
            )
            .join(ProxyType, ProxyCatalog.proxy_type_id == ProxyType.id)
            .join(Protocol, ProxyType.protocol_id == Protocol.id)
            .join(Operator, ProxyType.operator_id == Operator.id)
            .order_by(ProxyCatalog.id)
            .where(ProxyCatalog.available_amount>0)
        )
        result = await session.execute(stmt)
        rows = result.all()

        catalog_list = []
        for r in rows:
            catalog_list.append({
                "catalog_id": r.catalog_id,
                "protocol": r.protocol,
                "operator": r.operator,
                "speed": r.speed,
                "available_amount": r.available_amount,
                "price_per_week": r.price_per_week,
                "country_code": r.country_code
            })

    return catalog_list

async def get_all_catalog():
    await refresh_proxy_catalog()
    async with async_session() as session:
        stmt = (
            select(
                ProxyCatalog.id.label("catalog_id"),
                Protocol.value.label("protocol"),
                Operator.name.label("operator"),
                Operator.country_code.label("country_code"),
                ProxyType.speed.label("speed"),
                ProxyCatalog.available_amount.label("available_amount"),
                ProxyCatalog.price_per_week.label("price_per_week")
            )
            .join(ProxyType, ProxyCatalog.proxy_type_id == ProxyType.id)
            .join(Protocol, ProxyType.protocol_id == Protocol.id)
            .join(Operator, ProxyType.operator_id == Operator.id)
            .order_by(ProxyCatalog.id)
        )
        result = await session.execute(stmt)
        rows = result.all()

        catalog_list = []
        for r in rows:
            catalog_list.append({
                "catalog_id": r.catalog_id,
                "protocol": r.protocol,
                "operator": r.operator,
                "speed": r.speed,
                "available_amount": r.available_amount,
                "price_per_week": r.price_per_week,
                "country_code": r.country_code
            })

    return catalog_list

async def get_user_balance_by_tg_id(tg_id: int) -> int:
    async with async_session() as session:
        stmt = select(User.balance).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        return result.scalar()

async def get_user_id_by_tg_id(tg_id: int) -> int:
    async with async_session() as session:
        stmt = select(User.id).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        return result.scalar()


async def get_available_proxies_count_by_type_id(proxy_type_id: int) -> int:
    async with async_session() as session:
        stmt = select(func.count()).where(
            Proxy.proxy_type_id == proxy_type_id,
            Proxy.status_id == 1
        )
        result = await session.execute(stmt)
        return result.scalar_one()


async def get_all_operators():
    """
    Asynchronously retrieves a list of all operators.

    Returns a list of dictionaries with:
    - id (Operator.id)
    - name (Operator.name)
    - country_code (Operator.country_code)
    """
    async with async_session() as session:
        stmt = select(Operator.id, Operator.name, Operator.country_code)
        result = await session.execute(stmt)
        rows = result.all()

        operator_list = [{"id": row.id, "name": row.name, "country_code": row.country_code} for row in rows]

    return operator_list


async def get_all_protocols():
    """
    Асинхронно отримує список всіх протоколів.

    Повертає список словників з:
    - id (Protocol.id)
    - value (Protocol.value)
    """
    async with async_session() as session:
        stmt = select(Protocol.id, Protocol.value)
        result = await session.execute(stmt)
        rows = result.all()

        protocol_list = [{"id": row.id, "value": row.value} for row in rows]

    return protocol_list


async def get_operator_by_id(operator_id: int) -> dict:
    async with async_session() as session:
        stmt = select(Operator.id, Operator.name, Operator.country_code).where(Operator.id == operator_id)
        result = await session.execute(stmt)
        row = result.first()

    if row:
        return {"id": row.id, "name": row.name, "country_code": row.country_code}
    return {}


async def get_protocol_by_id(protocol_id: int) -> dict:
    async with async_session() as session:
        stmt = select(Protocol.id, Protocol.value).where(Protocol.id == protocol_id)
        result = await session.execute(stmt)
        row = result.first()

    if row:
        return {"id": row.id, "value": row.value}
    return {}


async def get_server_ips_list() -> list[str]:
    """
    Асинхронно отримує список всіх айпі серверів.

    Повертає список IP-адрес у форматі:
    - ['192.168.1.1', '10.0.0.1', ...]
    """
    async with async_session() as session:
        stmt = select(ProxyServer.ip)  # Обираємо тільки поле ip
        result = await session.execute(stmt)

        # Отримуємо плоский список IP-адрес
        ip_list = [ip for (ip,) in result.all()]

    return ip_list


async def get_server_id_by_ip(server_ip: str) -> Optional[int]:
    if not IPV4_PATTERN.match(server_ip):
        raise ValueError("Невірний формат IP-адреси")

    async with async_session() as session:
        try:
            # Створюємо запит до бази даних
            stmt = select(ProxyServer.id).where(ProxyServer.ip == server_ip)
            result = await session.execute(stmt)
            server = result.scalar_one_or_none()

            if server is None:
                logging.warning(f"Сервер з IP {server_ip} не знайдено в базі")
                return None

            return int(server)  # Повертаємо ID як ціле число

        except SQLAlchemyError as e:
            logging.error(f"Помилка бази даних при пошуку сервера {server_ip}: {e}")
            return None
        except Exception as e:
            logging.error(f"Невідома помилка при пошуку сервера: {e}")
            return None

async def get_first_available_proxy_by_type_id(proxy_type_id: int) -> Optional[Dict]:
    async with async_session() as session:
        stmt = (
            select(
                Proxy.id.label("id"),
                Proxy.internal_ip.label("internal_ip"),
                Proxy.server_id.label("server_id"),
                Proxy.status_id.label("status_id"),
                Proxy.proxy_type_id.label("proxy_type_id"),
                ProxyServer.ip.label("server_ip"),
                Status.value.label("status_name")
            )
            .select_from(Proxy)
            .join(ProxyServer, Proxy.server_id == ProxyServer.id)
            .join(ProxyType, Proxy.proxy_type_id == ProxyType.id)
            .join(Status, Proxy.status_id == Status.id)
            .where(
                Proxy.proxy_type_id == proxy_type_id,
                Proxy.status_id == 1
            )
            .order_by(Proxy.id)
            .limit(1)
        )

        result = await session.execute(stmt)
        return result.mappings().first()

async def get_first_available_port_id_by_server_id(server_id: int) -> int:
    async with async_session() as session:
        stmt = (
            select(
                ProxyPorts.id.label("id")
            )
            .where(
                ProxyPorts.server_id == server_id,
                ProxyPorts.status_id == 1
            )
            .order_by(ProxyPorts.id)
            .limit(1)
        )

        result = await session.execute(stmt)
        port = result.mappings().first()
        return port["id"] if port else None


async def get_current_proxies_price_per_week(catalog_id: int) -> Optional[int]:
    """Отримує ціну за тиждень для вказаного каталогу проксі.

    Args:
        catalog_id: ID каталогу проксі

    Returns:
        Ціна за тиждень або None, якщо каталог не знайдено
    """
    async with async_session() as session:
        stmt = (
            select(
                ProxyCatalog.price_per_week.label("price_per_week")
            )
            .where(
                ProxyCatalog.id == catalog_id
            )
        )

        result = await session.execute(stmt)
        price = result.mappings().first()
        return price["price_per_week"] if price else None


async def refresh_proxy_catalog():
    async with async_session() as session:
        try:
            # 1. Отримуємо всі типи проксі
            proxy_types = await session.execute(select(ProxyType.id))
            all_type_ids = {t[0] for t in proxy_types.all()}

            if not all_type_ids:
                return  # Немає типів проксі для оновлення

            # 2. Отримуємо поточні записи каталогу
            catalog_items = await session.execute(select(ProxyCatalog))
            existing_catalogs = catalog_items.scalars().all()
            existing_type_ids = {c.proxy_type_id for c in existing_catalogs}

            # 3. Додаємо нові каталоги для типів, яких ще немає
            new_types_to_add = all_type_ids - existing_type_ids
            for type_id in new_types_to_add:
                count = await get_available_proxies_count_by_type_id(type_id)
                new_catalog = ProxyCatalog(
                    proxy_type_id=type_id,
                    available_amount=count,
                )
                session.add(new_catalog)

            for catalog in existing_catalogs:
                count = await get_available_proxies_count_by_type_id(catalog.proxy_type_id)
                catalog.available_amount = count

            await session.commit()

        except Exception as e:
            await session.rollback()
            logging.error(f"Помилка при оновленні каталогу проксі: {e}")
            raise


async def get_user_proxies_list(user_id: int):
    async with async_session() as session:
        stmt = (
            select(
                ProxyRental.id.label("rental_id"),
                ProxyServer.ip.label("ip"),
                ProxyPorts.port.label("port"),
                ProxyRental.login.label("login"),
                ProxyRental.password.label("password"),
                Protocol.value.label("protocol"),
                Operator.name.label("operator"),
                Operator.country_code.label("country_code"),
                ProxyRental.purchase_date,
                ProxyRental.expire_date
            )
            .join(Proxy, ProxyRental.proxy_id == Proxy.id)
            .join(ProxyServer, Proxy.server_id == ProxyServer.id)
            .join(ProxyPorts, ProxyRental.port_id == ProxyPorts.id)
            .join(ProxyType, Proxy.proxy_type_id == ProxyType.id)
            .join(Protocol, ProxyType.protocol_id == Protocol.id)
            .join(Operator, ProxyType.operator_id == Operator.id)
            .where(ProxyRental.user_id == user_id)
            .order_by(ProxyRental.id)
        )

        result = await session.execute(stmt)
        rows = result.all()

        proxies_list = []
        for r in rows:
            proxies_list.append({
                "rental_id": r.rental_id,
                "ip": r.ip,
                "port": r.port,
                "login": r.login,
                "password": r.password,
                "protocol": r.protocol,
                "operator": r.operator,
                "country_code": r.country_code,
                "purchase_date": r.purchase_date,
                "expire_date": r.expire_date
            })

    return proxies_list

async def get_task_status(task_id: int) -> str:
    async with async_session() as session:
        result = await session.execute(
            select(ProxyTaskQueue.status).where(ProxyTaskQueue.id == task_id)
        )
        status = result.scalar_one_or_none()
        return status