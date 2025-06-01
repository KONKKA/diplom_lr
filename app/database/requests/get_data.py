"""Database query operations for proxy management system.

This module contains asynchronous functions for interacting with the database
to manage proxies, users, and related entities.
"""

import logging
from typing import List, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from app.database.db import async_session
from app.database.models import Proxy, Protocol, Operator, Status, ProxyType, ProxyCatalog, User, ProxyServer, \
    ProxyPorts, ProxyRental, ProxyTaskQueue
from app.utils.constants import IPV4_PATTERN


async def get_all_proxies_info() -> List[Dict]:
    """Retrieves information about all proxies in the system.

    Returns:
        A list of dictionaries containing proxy information with keys:
        - id: Proxy ID
        - server_ip: Server IP address
        - internal_ip: Internal IP address
        - protocol: Protocol type
        - operator: Operator name
        - country: Country code
        - status: Proxy status
    """
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
    """Retrieves a specific catalog item by its ID.

    Args:
        proxy_catalog_id: The ID of the catalog item to retrieve.

    Returns:
        A dictionary containing catalog item information with keys:
        - id: Catalog item ID
        - country_code: Country code
        - operator: Operator name
        - protocol: Protocol type
        - available_amount: Number of available proxies
        - price_per_week: Weekly price
        - proxy_type_id: Proxy type ID
        or None if not found.
    """
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


async def get_available_catalog() -> List[Dict]:
    """Retrieves all available proxy catalog items.

    First refreshes the catalog availability counts.

    Returns:
        A list of dictionaries containing available catalog items with keys:
        - catalog_id: Catalog item ID
        - protocol: Protocol type
        - operator: Operator name
        - country_code: Country code
        - speed: Proxy speed
        - available_amount: Number of available proxies
        - price_per_week: Weekly price
    """
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


async def get_all_catalog() -> List[Dict]:
    """Retrieves all proxy catalog items, regardless of availability.

    First refreshes the catalog availability counts.

    Returns:
        A list of dictionaries containing all catalog items with keys:
        - catalog_id: Catalog item ID
        - protocol: Protocol type
        - operator: Operator name
        - country_code: Country code
        - speed: Proxy speed
        - available_amount: Number of available proxies
        - price_per_week: Weekly price
    """
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
    """Retrieves a user's balance by their Telegram ID.

    Args:
        tg_id: The Telegram ID of the user.

    Returns:
        The user's balance as an integer.
    """
    async with async_session() as session:
        stmt = select(User.balance).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        return result.scalar()


async def get_user_id_by_tg_id(tg_id: int) -> int:
    """Retrieves a user's database ID by their Telegram ID.

    Args:
        tg_id: The Telegram ID of the user.

    Returns:
        The user's database ID as an integer.
    """
    async with async_session() as session:
        stmt = select(User.id).where(User.tg_id == tg_id)
        result = await session.execute(stmt)
        return result.scalar()


async def get_available_proxies_count_by_type_id(proxy_type_id: int) -> int:
    """Counts available proxies of a specific type.

    Args:
        proxy_type_id: The ID of the proxy type to count.

    Returns:
        The number of available proxies of the specified type.
    """
    async with async_session() as session:
        stmt = select(func.count()).where(
            Proxy.proxy_type_id == proxy_type_id,
            Proxy.status_id == 1
        )
        result = await session.execute(stmt)
        return result.scalar_one()


async def get_all_operators() -> List[Dict]:
    """Retrieves a list of all operators.

    Returns:
        A list of dictionaries with operator information:
        - id: Operator ID
        - name: Operator name
        - country_code: Country code
    """
    async with async_session() as session:
        stmt = select(Operator.id, Operator.name, Operator.country_code)
        result = await session.execute(stmt)
        rows = result.all()

        operator_list = [{"id": row.id, "name": row.name, "country_code": row.country_code} for row in rows]

    return operator_list


async def get_all_protocols() -> List[Dict]:
    """Retrieves a list of all protocols.

    Returns:
        A list of dictionaries with protocol information:
        - id: Protocol ID
        - value: Protocol value/name
    """
    async with async_session() as session:
        stmt = select(Protocol.id, Protocol.value)
        result = await session.execute(stmt)
        rows = result.all()

        protocol_list = [{"id": row.id, "value": row.value} for row in rows]

    return protocol_list


async def get_operator_by_id(operator_id: int) -> Dict:
    """Retrieves an operator by its ID.

    Args:
        operator_id: The ID of the operator to retrieve.

    Returns:
        A dictionary with operator information:
        - id: Operator ID
        - name: Operator name
        - country_code: Country code
        or an empty dictionary if not found.
    """
    async with async_session() as session:
        stmt = select(Operator.id, Operator.name, Operator.country_code).where(Operator.id == operator_id)
        result = await session.execute(stmt)
        row = result.first()

    if row:
        return {"id": row.id, "name": row.name, "country_code": row.country_code}
    return {}


async def get_protocol_by_id(protocol_id: int) -> Dict:
    """Retrieves a protocol by its ID.

    Args:
        protocol_id: The ID of the protocol to retrieve.

    Returns:
        A dictionary with protocol information:
        - id: Protocol ID
        - value: Protocol value/name
        or an empty dictionary if not found.
    """
    async with async_session() as session:
        stmt = select(Protocol.id, Protocol.value).where(Protocol.id == protocol_id)
        result = await session.execute(stmt)
        row = result.first()

    if row:
        return {"id": row.id, "value": row.value}
    return {}


async def get_server_ips_list() -> List[str]:
    """Retrieves a list of all server IP addresses.

    Returns:
        A list of IP addresses as strings.
    """
    async with async_session() as session:
        stmt = select(ProxyServer.ip)
        result = await session.execute(stmt)
        ip_list = [ip for (ip,) in result.all()]

    return ip_list


async def get_server_id_by_ip(server_ip: str) -> Optional[int]:
    """Retrieves a server ID by its IP address.

    Args:
        server_ip: The IP address of the server.

    Returns:
        The server ID as an integer, or None if not found.

    Raises:
        ValueError: If the provided IP address is invalid.
    """
    if not IPV4_PATTERN.match(server_ip):
        raise ValueError("Invalid IP address format")

    async with async_session() as session:
        try:
            stmt = select(ProxyServer.id).where(ProxyServer.ip == server_ip)
            result = await session.execute(stmt)
            server = result.scalar_one_or_none()

            if server is None:
                logging.warning(f"Server with IP {server_ip} not found in database")
                return None

            return int(server)

        except SQLAlchemyError as e:
            logging.error(f"Database error when searching for server {server_ip}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unknown error when searching for server: {e}")
            return None


async def get_first_available_proxy_by_type_id(proxy_type_id: int) -> Optional[Dict]:
    """Retrieves the first available proxy of a specific type.

    Args:
        proxy_type_id: The ID of the proxy type to retrieve.

    Returns:
        A dictionary with proxy information:
        - id: Proxy ID
        - internal_ip: Internal IP address
        - server_id: Server ID
        - status_id: Status ID
        - proxy_type_id: Proxy type ID
        - server_ip: Server IP address
        - status_name: Status name
        or None if no available proxy found.
    """
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


async def get_first_available_port_id_by_server_id(server_id: int) -> Optional[int]:
    """Retrieves the first available port ID for a given server.

    Args:
        server_id: The ID of the server to check.

    Returns:
        The port ID as an integer, or None if no available port found.
    """
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
    """Retrieves the weekly price for a specific catalog item.

    Args:
        catalog_id: The ID of the catalog item.

    Returns:
        The weekly price as an integer, or None if catalog item not found.
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


async def refresh_proxy_catalog() -> None:
    """Refreshes the proxy catalog by updating availability counts.

    This function:
    1. Gets all proxy types
    2. Checks existing catalog items
    3. Adds new catalog items for any missing proxy types
    4. Updates availability counts for all catalog items

    Raises:
        Exception: If any error occurs during the database operations.
    """
    async with async_session() as session:
        try:
            # 1. Get all proxy types
            proxy_types = await session.execute(select(ProxyType.id))
            all_type_ids = {t[0] for t in proxy_types.all()}

            if not all_type_ids:
                return  # No proxy types to update

            # 2. Get current catalog entries
            catalog_items = await session.execute(select(ProxyCatalog))
            existing_catalogs = catalog_items.scalars().all()
            existing_type_ids = {c.proxy_type_id for c in existing_catalogs}

            # 3. Add new catalogs for missing types
            new_types_to_add = all_type_ids - existing_type_ids
            for type_id in new_types_to_add:
                count = await get_available_proxies_count_by_type_id(type_id)
                new_catalog = ProxyCatalog(
                    proxy_type_id=type_id,
                    available_amount=count,
                )
                session.add(new_catalog)

            # 4. Update availability counts
            for catalog in existing_catalogs:
                count = await get_available_proxies_count_by_type_id(catalog.proxy_type_id)
                catalog.available_amount = count

            await session.commit()

        except Exception as e:
            await session.rollback()
            logging.error(f"Error updating proxy catalog: {e}")
            raise


async def get_user_proxies_list(user_id: int) -> List[Dict]:
    """Retrieves a list of proxies rented by a specific user.

    Args:
        user_id: The ID of the user.

    Returns:
        A list of dictionaries containing proxy rental information:
        - rental_id: Rental ID
        - ip: Server IP address
        - port: Port number
        - login: Authentication login
        - password: Authentication password
        - protocol: Protocol type
        - operator: Operator name
        - country_code: Country code
        - purchase_date: Date of purchase
        - expire_date: Expiration date
    """
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


async def get_task_status(task_id: int) -> Optional[str]:
    """Retrieves the status of a task by its ID.

    Args:
        task_id: The ID of the task.

    Returns:
        The task status as a string, or None if task not found.
    """
    async with async_session() as session:
        result = await session.execute(
            select(ProxyTaskQueue.status).where(ProxyTaskQueue.id == task_id)
        )
        status = result.scalar_one_or_none()
        return status