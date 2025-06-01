from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton)

from config import SUPPORT_CHAT

def get_menu_buttons(is_admin: bool = False) -> list:
    buttons = [
        [
            InlineKeyboardButton(
                text="🛍️ Каталог проксі",
                callback_data="proxy_catalog"
            ),
            InlineKeyboardButton(
                text="📊 Мої проксі",
                callback_data="my_proxies"
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 Поповнити баланс",
                callback_data="top_up_balance"
            ),
            InlineKeyboardButton(
                text="🛠️ Техпідтримка",
                url=f"https://t.me/{SUPPORT_CHAT}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙ Налаштування",
                callback_data="profile_settings"
            )
        ]
    ]

    if is_admin:
        # Додаємо окремий рядок з кнопкою для адміна
        buttons.append([
            InlineKeyboardButton(
                text="🛡️ Адмін панель",
                callback_data="admin_panel"
            )
        ])

    return buttons

def get_back_reply_button() -> list:
    return [
        [
            KeyboardButton(
                text="Повернутися в меню"
            )
        ]
    ]

def get_support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🛠️ Техпідтримка",
                    url=f"https://t.me/{SUPPORT_CHAT}"
                )
    ]])

