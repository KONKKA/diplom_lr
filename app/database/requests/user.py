import logging

from sqlite3 import IntegrityError
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError


from app.database.db import async_session
from app.database.models import User
from sqlalchemy import select, update

async def user_exists(tg_id: int) -> bool:
    async with async_session() as session:
        result = await session.scalar(select(User).where(User.tg_id == tg_id))
        print(result is not None)
        return result is not None

async def add_user(tg_id: int, first_name: str, last_name: str, phone_number: str, username: str):
    if await user_exists(tg_id):
        raise ValueError(f"Користувач з ID:{tg_id} вже існує. Зверніться в підтримку!")

    async with async_session() as session:
        new_user = User(
            tg_id=tg_id,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            username=username
        )
        session.add(new_user)
        try:
            await session.commit()
            print(f"New user created: {new_user}")
        except IntegrityError as e:
            await session.rollback()
            raise RuntimeError(f"Не вдалося додати користувача: {e}")

async def get_user(tg_id: int) -> User:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None:
            raise ValueError(f"Користувач з ID:{tg_id} не існує. Зверніться в підтримку!")
        else:
            return user


async def update_user(
        tg_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        username: Optional[str] = None
) -> bool:
    """
    Оновлює дані користувача

    :param tg_id: Telegram ID користувача
    :param first_name: Нове ім'я (опціонально)
    :param last_name: Нове прізвище (опціонально)
    :param phone_number: Новий номер телефону (опціонально)
    :return: True при успіху, False при помилці
    """
    update_data = {}
    if first_name is not None:
        update_data["first_name"] = first_name.strip()
    if last_name is not None:
        update_data["last_name"] = last_name.strip()
    if last_name is None:
        update_data["last_name"] = ""
    if username is None:
        update_data["last_name"] = ""
    if phone_number is not None:
        update_data["phone_number"] = phone_number.strip()

    try:
        async with async_session() as session:
            # Оптимізований запит без попереднього отримання об'єкта
            result = await session.execute(
                update(User)
                .where(User.tg_id == tg_id)
                .values(**update_data)
            )
            await session.commit()

            if result.rowcount == 0:
                raise ValueError(f"Користувач з ID {tg_id} не знайдений")

            return True
    except SQLAlchemyError as e:
        await session.rollback()
        logging.error(f"Помилка оновлення користувача {tg_id}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Критична помилка: {str(e)}")
        return False