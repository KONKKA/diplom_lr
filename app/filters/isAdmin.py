from aiogram import types
from aiogram.filters import BaseFilter

from config import ADMINS

class IsAdmin(BaseFilter):
    """
    Filter that checks if the message sender is an administrator.

    Returns:
        bool: True if the sender's user ID is in the ADMINS set, False otherwise.
    """
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in ADMINS