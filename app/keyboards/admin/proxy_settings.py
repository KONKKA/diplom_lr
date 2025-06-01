from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_pagination_keyboard(
    page: int,
    total_pages: int,
    back_callback_data: str = "admin_panel",
    additional_button: Optional[InlineKeyboardButton] = None
) -> InlineKeyboardMarkup:
    keyboard = []

    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="⬅️ Попередня", callback_data=f"prev_{page - 1}")
        )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="Наступна ➡️", callback_data=f"next_{page + 1}")
        )
    if pagination_buttons:
        keyboard.append(pagination_buttons)

    if additional_button:
        keyboard.append([additional_button])

    keyboard.append([
        InlineKeyboardButton(text="🔙 Повернутися", callback_data=back_callback_data)
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)