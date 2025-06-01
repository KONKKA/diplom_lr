from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_back_keyboard(callback_data: str, text: Optional[str] = "🔙 Повернутися") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=callback_data
                )
            ]
        ]
    )


def get_confirm_or_cancel_keyboard(confirm_callback_data: str, decline_callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Підтвердити",
                callback_data=confirm_callback_data),
            InlineKeyboardButton(
                text="❌ Скасувати",
                callback_data=decline_callback_data)
        ]
    ])
