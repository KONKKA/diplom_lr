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


async def save_proxies_from_fsm(fsm_data: Dict[str, Any]) -> str:
    operator_id: int = fsm_data["operator_id"]
    protocol_id: int = fsm_data["protocol_id"]
    server_ip: str = fsm_data["server_ip"]
    internal_ips: list[str] = fsm_data["internal_ips"]

    async with async_session() as session:
        try:
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

            proxy_server = await session.scalar(
                select(ProxyServer).where(ProxyServer.ip == server_ip)
            )
            if not proxy_server:
                return "❌ Сервер не знайдено"

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
                # Валідація IP
                if not IPV4_PATTERN.match(internal_ip):
                    results.append(f"⛔ {internal_ip} - невалідна IP-адреса")
                    invalid_count += 1
                    continue

                # Перевірка на дублікат
                if internal_ip in existing_ips:
                    results.append(f"⚠️ {internal_ip} - вже існує")
                    duplicate_count += 1
                    continue

                # Додаємо новий проксі
                new_proxy = Proxy(
                    server_id=proxy_server.id,
                    internal_ip=internal_ip,
                    proxy_type_id=proxy_type.id,
                    status_id=1,  # Стан "Активний"
                )
                new_proxies.append(new_proxy)
                existing_ips.add(internal_ip)
                results.append(f"✅ {internal_ip} - успішно додано")
                added_count += 1

            if new_proxies:
                session.add_all(new_proxies)
                await session.commit()

            # Формуємо підсумковий звіт
            report = (
                    "\n".join(results) +
                    f"\n\n📊 Підсумок:\n"
                    f"Додано: {added_count}\n"
                    f"Дублікатів: {duplicate_count}\n"
                    f"Невалідних IP: {invalid_count}"
            )

            return report

        except SQLAlchemyError as e:
            await session.rollback()
            logging.error(f"Database error: {e}")
            return f"❌ Помилка бази даних: {e}"
        except Exception as e:
            await session.rollback()
            logging.error(f"Unexpected error: {e}")
            return f"❌ Невідома помилка: {e}"

async def save_server_ip(server_ip: str) -> bool:
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
    ACTIVE = ("Available", 1)
    RENTED = ("Rented", 2)
    UNAVAILABLE = ("Unavailable", 3)

    @classmethod
    def get_status_id(cls, status_name: str) -> Optional[int]:
        for status in cls:
            if status.value[0].lower() == status_name.lower():
                return status.value[1]
        return None


async def update_proxy_status(proxy_id: int, status: str = "Available") -> Optional[bool]:
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
    async with async_session() as session:
        try:
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
                        results.append(f"⛔ {port_str} - невалідний (має бути 1-65535)")
                        invalid_count += 1
                        continue

                    # Перевірка на дублікат
                    if port in existing_ports:
                        results.append(f"⚠️ {port} - вже існує")
                        duplicate_count += 1
                        continue

                    # Додавання нового порту
                    await session.execute(
                        insert(ProxyPorts)
                        .values(
                            server_id=server_id,
                            port=port,
                            status_id=1)
                    )
                    results.append(f"✅ {port} - успішно додано")
                    added_count += 1
                    existing_ports.add(port)
                except ValueError:
                    results.append(f"⛔ {port_str} - нечислове значення")
                    invalid_count += 1

            await session.commit()


            summary = (
                    "\n".join(results) +
                    "\n\n📊 Підсумок:\n" +
                    f"Додано: {added_count}\n" +
                    f"Дублікатів: {duplicate_count}\n" +
                    f"Невалідних: {invalid_count}"
            )

            return summary

        except SQLAlchemyError as e:
            await session.rollback()
            logging.error(f"Database error: {e}")
            return f"❌ Критична помилка бази даних: {e}"
        except Exception as e:
            await session.rollback()
            logging.error(f"Unexpected error: {e}")
            return f"❌ Невідома помилка: {e}"


async def create_proxy_rental(
        tg_id: int,
        proxy_id: int,
        term: int,  # term in weeks
        port_id: int,
        login: str,
        password: str,
) -> ProxyRental:

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

    async with async_session() as session:
        try:
            # 1. Отримуємо поточний баланс
            current_balance = await get_user_balance_by_tg_id(tg_id)

            # Якщо користувача не знайдено або баланс None
            if current_balance is None:
                return False

            # 2. Перевіряємо чи достатньо коштів
            if current_balance < amount:
                return False

            # 3. Оновлюємо баланс
            async with session.begin():
                update_stmt = (
                    update(User)
                    .where(User.tg_id == tg_id)
                    .values(balance=User.balance - amount)
                )
                await session.execute(update_stmt)

            return True

        except SQLAlchemyError as e:
            print(f"Помилка бази даних: {e}")
            return False
        except Exception as e:
            print(f"Неочікувана помилка: {e}")
            return False