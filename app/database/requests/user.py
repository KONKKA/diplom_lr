import logging

from sqlite3 import IntegrityError
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError


from app.database.db import async_session
from app.database.models import User
from sqlalchemy import select, update

async def user_exists(tg_id: int) -> bool:
    """
    Check if a user exists by their Telegram ID.

    Args:
        tg_id (int): Telegram user ID.

    Returns:
        bool: True if user exists, False otherwise.
    """
    async with async_session() as session:
        result = await session.scalar(select(User).where(User.tg_id == tg_id))
        print(result is not None)
        return result is not None


async def add_user(tg_id: int, first_name: str, last_name: str, phone_number: str, username: str):
    """
    Add a new user to the database.

    Args:
        tg_id (int): Telegram user ID.
        first_name (str): User's first name.
        last_name (str): User's last name.
        phone_number (str): User's phone number.
        username (str): User's Telegram username.

    Raises:
        ValueError: If user with given tg_id already exists.
        RuntimeError: If insertion fails due to database constraints.
    """
    if await user_exists(tg_id):
        raise ValueError(f"User with ID:{tg_id} already exists. Please contact support!")

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
            raise RuntimeError(f"Failed to add user: {e}")


async def get_user(tg_id: int) -> User:
    """
    Retrieve a user by their Telegram ID.

    Args:
        tg_id (int): Telegram user ID.

    Returns:
        User: The User object from the database.

    Raises:
        ValueError: If user with given tg_id does not exist.
    """
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None:
            raise ValueError(f"User with ID:{tg_id} does not exist. Please contact support!")
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
    Update user data by Telegram ID.

    Args:
        tg_id (int): Telegram user ID.
        first_name (Optional[str]): New first name (optional).
        last_name (Optional[str]): New last name (optional).
        phone_number (Optional[str]): New phone number (optional).
        username (Optional[str]): New username (optional).

    Returns:
        bool: True if update was successful, False otherwise.

    Notes:
        Fields are updated only if their corresponding parameters are not None.
        To clear a field (e.g., last_name), pass an empty string explicitly.
        If no fields are provided for update, the function returns False.
    """
    update_data = {}

    if first_name is not None:
        update_data["first_name"] = first_name.strip()

    if last_name is not None:
        update_data["last_name"] = last_name.strip()

    if username is not None:
        update_data["username"] = username.strip()

    if phone_number is not None:
        update_data["phone_number"] = phone_number.strip()

    if not update_data:
        # No data to update
        logging.warning(f"No update data provided for user {tg_id}")
        return False

    try:
        async with async_session() as session:
            result = await session.execute(
                update(User)
                .where(User.tg_id == tg_id)
                .values(**update_data)
            )
            await session.commit()

            if result.rowcount == 0:
                raise ValueError(f"User with tg_id {tg_id} not found")

            return True
    except SQLAlchemyError as e:
        await session.rollback()
        logging.error(f"Error updating user {tg_id}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Critical error: {str(e)}")
        return False
