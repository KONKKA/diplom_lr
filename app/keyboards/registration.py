from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton


def get_accept_terms_button() -> list:
    return [
        [
            InlineKeyboardButton(
                text="📄 Ознайомитись з угодою",
                web_app=WebAppInfo(url="https://habr.com"))
        ],
        [
            InlineKeyboardButton(
                text="✅ Погоджуюсь з умовами",
                callback_data="accept_terms"
            )
        ]
    ]

def get_contact_reply_button() -> list:
    return [
        [
            KeyboardButton(
                text="📱 Поділитися контактом",
                request_contact=True
            )
        ]
    ]

def get_contact_keyboard_settings():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Поділитися контактом",
                    request_contact=True
                )
            ],
            [
                KeyboardButton(
                    text="Повернутися в меню"
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )



def get_registration_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Зареєструватися",
                    callback_data="registration")
            ]
        ]
    )
