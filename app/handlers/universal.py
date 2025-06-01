from typing import Union
from aiogram.types import Message, CallbackQuery

from app.keyboards.universal_keyboards import get_confirm_or_cancel_keyboard


async def send_confirmation_request_panel(
        target: Union[Message, CallbackQuery],
        text: str,
        confirm_callback_data: str,
        decline_callback_data: str
):

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_confirm_or_cancel_keyboard(confirm_callback_data,decline_callback_data)
        )
        await target.answer()

    elif isinstance(target, Message):
        await target.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_confirm_or_cancel_keyboard(confirm_callback_data,decline_callback_data)
        )