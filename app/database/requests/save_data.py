"""Database operations for proxy management system.

This module contains functions for creating, updating, and managing proxies,
servers, ports, operators, and user rentals in the database.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Any

from sqlalchemy import select, update, insert
from sqlalchemy.exc import SQLAlchemyError

from app.database.db import async_session
from app.database.models import Proxy, Operator, ProxyType, ProxyServer, \
    ProxyPorts, ProxyRental, User
from app.database.requests.get_data import get_user_balance_by_tg_id, get_user_id_by_tg_id
from app.utils.constants import IPV4_PATTERN


async def save_operator_to_db(country_code: str, operator_name: str) -> bool:
    """Saves a new operator to the database if it doesn't already exist.

    Args:
        country_code: The country code for the operator (will be converted to uppercase).
        operator_name: The name of the operator (will be converted to uppercase).

    Returns:
        bool: True if the operator was created, False if it already exists.

    Example:
        >>> await save_operator_to_db("US", "AT&T")
        True
    """
    async with async_session() as session:
        stmt = select(Operator).where(
            Operator.country_code == country_code.upper(),
            Operator.name== operator_name.upper(),
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return False

        new_operator = Operator(
            name=operator_name,
            country_code=country_code.upper()
        )
        session.add(new_operator)
        await session.commit()
        return True


async def save_proxies_from_fsm(data: Dict[str, Any]) -> str:
    """Saves multiple proxies to the database from FSM (Finite State Machine) data.

    Args:
        data: A dictionary containing:
            - operator_id: ID of the operator
            - protocol_id: ID of the protocol
            - server_ip: Server IP address
            - internal_ips: List of internal IP addresses to add

    Returns:
        str: A detailed report of the operation including:
             - Successfully added proxies
             - Duplicate proxies
             - Invalid IP addresses
             - Summary statistics

    Raises:
        SQLAlchemyError: If there's a database error during the operation.

    Example:
        >>> data = {
        ...     "operator_id": 1,
        ...     "protocol_id": 2,
        ...     "server_ip": "192.168.1.1",
        ...     "internal_ips": ["10.0.0.1", "10.0.0.2"]
        ... }
        >>> await save_proxies_from_fsm(data)
    """
    operator_id: int = data["operator_id"]
    protocol_id: int = data["protocol_id"]
    server_ip: str = data["server_ip"]
    internal_ips: list[str] = data["internal_ips"]

    async with async_session() as session:
        try:
            # Check/create proxy type
            proxy_type = await session.scalar(
                select(ProxyType).where(
                    ProxyType.operator_id == operator_id,
                    ProxyType.protocol_id == protocol_id
                )
            )

            if not proxy_type:
                proxy_type = ProxyType(
                    operator_id=operator_id,
                    protocol_id=protocol_id
                )
                session.add(proxy_type)
                await session.flush()

            # Verify server exists
            proxy_server = await session.scalar(
                select(ProxyServer).where(ProxyServer.ip == server_ip)
            )
            if not proxy_server:
                return "❌ Server not found"

            # Process each IP address
            existing_ips = set(await session.scalars(
                select(Proxy.internal_ip).where(
                    Proxy.server_id == proxy_server.id
                )
            ))

            results = []
            added_count = 0
            duplicate_count = 0
            invalid_count = 0
            new_proxies = []

            for internal_ip in internal_ips:
                # Validate IP format
                if not IPV4_PATTERN.match(internal_ip):
                    results.append(f"⛔ {internal_ip} - invalid IP address")
                    invalid_count += 1
                    continue

                # Check for duplicates
                if internal_ip in existing_ips:
                    results.append(f"⚠️ {internal_ip} - already exists")
                    duplicate_count += 1
                    continue

                # Add new proxy
                new_proxy = Proxy(
                    server_id=proxy_server.id,
                    internal_ip=internal_ip,
                    proxy_type_id=proxy_type.id,
                    status_id=1,  # "Active" status
                )
                new_proxies.append(new_proxy)
                existing_ips.add(internal_ip)
                results.append(f"✅ {internal_ip} - successfully added")
                added_count += 1

            if new_proxies:
                session.add_all(new_proxies)
                await session.commit()

            # Generate report
            report = (
                    "\n".join(results) +
                    f"\n\n📊 Summary:\n"
                    f"Added: {added_count}\n"
                    f"Duplicates: {duplicate_count}\n"
                    f"Invalid IPs: {invalid_count}"
            )

            return report

        except SQLAlchemyError as e:
            await session.rollback()
            logging.error(f"Database error: {e}")
            return f"❌ Database error: {e}"
        except Exception as e:
            await session.rollback()
            logging.error(f"Unexpected error: {e}")
            return f"❌ Unexpected error: {e}"


async def save_server_ip(server_ip: str) -> bool:
    """Saves a new server IP address to the database if it doesn't exist.

    Args:
        server_ip: The IP address of the server to add.

    Returns:
        bool: True if the server was added, False if it already exists.
    """
    async with async_session() as session:
        stmt = select(ProxyServer).where(
            ProxyServer.ip == server_ip
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return False

        new_server = ProxyServer(ip=server_ip)
        session.add(new_server)
        await session.commit()
        return True


class ProxyStatus(Enum):
    """Enumeration of possible proxy statuses.

    Attributes:
        ACTIVE: Proxy is available for rental
        RENTED: Proxy is currently rented
        UNAVAILABLE: Proxy is unavailable
    """
    ACTIVE = ("Available", 1)
    RENTED = ("Rented", 2)
    UNAVAILABLE = ("Unavailable", 3)

    @classmethod
    def get_status_id(cls, status_name: str) -> Optional[int]:
        """Gets the status ID for a given status name.

        Args:
            status_name: The name of the status (case-insensitive).

        Returns:
            The corresponding status ID or None if not found.
        """
        for status in cls:
            if status.value[0].lower() == status_name.lower():
                return status.value[1]
        return None


async def update_proxy_status(proxy_id: int, status: str = "Available") -> Optional[bool]:
    """Updates the status of a specific proxy.

    Args:
        proxy_id: The ID of the proxy to update.
        status: The new status (default: "Available").

    Returns:
        bool: True if update was successful, False if failed.
        None: If the status name is invalid.
    """
    status_id = ProxyStatus.get_status_id(status)
    if status_id is None:
        return None

    async with async_session() as session:
        try:
            stmt = (
                update(Proxy)
                .where(Proxy.id == proxy_id)
                .values(status_id=status_id)
            )

            result = await session.execute(stmt)
            await session.commit()

            return result.rowcount > 0

        except SQLAlchemyError as e:
            await session.rollback()
            logging.error(f"Failed to update proxy status: {e}")
            return False


async def update_port_status(port_id: int, status: str = "Available") -> Optional[bool]:
    """Updates the status of a specific port.

    Args:
        port_id: The ID of the port to update.
        status: The new status (default: "Available").

    Returns:
        bool: True if update was successful, False if failed.
        None: If the status name is invalid.
    """
    status_id = ProxyStatus.get_status_id(status)
    async with async_session() as session:
        try:
            stmt = (
                update(ProxyPorts)
                .where(ProxyPorts.id == port_id)
                .values(status_id=status_id)
            )

            result = await session.execute(stmt)
            await session.commit()

            return result.rowcount > 0

        except SQLAlchemyError as e:
            await session.rollback()
            logging.error(f"Failed to update port status: {e}")
            return False


async def save_port_list(port_list: list[str], server_id: int) -> Optional[str]:
    """Saves a list of ports for a specific server.

    Args:
        port_list: List of port numbers as strings.
        server_id: The ID of the server these ports belong to.

    Returns:
        str: A detailed report of the operation including:
             - Successfully added ports
             - Duplicate ports
             - Invalid ports
             - Summary statistics
        None: If there was a critical error.

    Raises:
        SQLAlchemyError: If there's a database error.
    """
    async with async_session() as session:
        try:
            # Get existing ports for this server
            existing_ports_result = await session.execute(
                select(ProxyPorts.port)
                .where(ProxyPorts.server_id == server_id)
            )
            existing_ports = {port[0] for port in existing_ports_result}

            results = []
            added_count = 0
            duplicate_count = 0
            invalid_count = 0

            for port_str in port_list:
                try:
                    port = int(port_str)
                    if not (1 <= port <= 65535):
                        results.append(f"⛔ {port_str} - invalid (must be 1-65535)")
                        invalid_count += 1
                        continue

                    # Check for duplicates
                    if port in existing_ports:
                        results.append(f"⚠️ {port} - already exists")
                        duplicate_count += 1
                        continue

                    # Add new port
                    await session.execute(
                        insert(ProxyPorts)
                        .values(
                            server_id=server_id,
                            port=port,
                            status_id=1)
                    )
                    results.append(f"✅ {port} - successfully added")
                    added_count += 1
                    existing_ports.add(port)
                except ValueError:
                    results.append(f"⛔ {port_str} - non-numeric value")
                    invalid_count += 1

            await session.commit()

            summary = (
                    "\n".join(results) +
                    "\n\n📊 Summary:\n" +
                    f"Added: {added_count}\n" +
                    f"Duplicates: {duplicate_count}\n" +
                    f"Invalid: {invalid_count}"
            )

            return summary

        except SQLAlchemyError as e:
            await session.rollback()
            logging.error(f"Database error: {e}")
            return f"❌ Critical database error: {e}"
        except Exception as e:
            await session.rollback()
            logging.error(f"Unexpected error: {e}")
            return f"❌ Unknown error: {e}"


async def create_proxy_rental(
        tg_id: int,
        proxy_id: int,
        term: int,
        port_id: int,
        login: str,
        password: str,
) -> ProxyRental:
    """Creates a new proxy rental record.

    Args:
        tg_id: Telegram ID of the user renting the proxy.
        proxy_id: ID of the proxy being rented.
        term: Rental duration in weeks.
        port_id: ID of the port being assigned.
        login: Authentication login for the proxy.
        password: Authentication password for the proxy.

    Returns:
        ProxyRental: The newly created rental record.

    Note:
        Automatically calculates expiration date based on current date + term.
    """
    async with async_session() as session:
        purchase_date = datetime.now()
        expire_date = purchase_date + timedelta(weeks=term)
        user_id = await get_user_id_by_tg_id(tg_id)

        new_rental = ProxyRental(
            user_id=user_id,
            proxy_id=proxy_id,
            purchase_date=purchase_date,
            expire_date=expire_date,
            port_id=port_id,
            login=login,
            password=password
        )
        session.add(new_rental)
        await session.commit()
        await session.refresh(new_rental)

        return new_rental


async def decrease_user_balance(tg_id: int, amount: float) -> bool:
    """Decreases a user's balance by the specified amount.

    Args:
        tg_id: Telegram ID of the user.
        amount: Amount to deduct from the balance.

    Returns:
        bool: True if the operation was successful, False if:
              - User not found
              - Insufficient balance
              - Database error occurred
    """
    async with async_session() as session:
        try:
            # Check current balance
            current_balance = await get_user_balance_by_tg_id(tg_id)

            # Return False if user not found or balance is None
            if current_balance is None:
                return False

            # Check sufficient funds
            if current_balance < amount:
                return False

            # Update balance
            async with session.begin():
                update_stmt = (
                    update(User)
                    .where(User.tg_id == tg_id)
                    .values(balance=User.balance - amount)
                )
                await session.execute(update_stmt)

            return True

        except SQLAlchemyError as e:
            logging.error(f"Database error: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return False