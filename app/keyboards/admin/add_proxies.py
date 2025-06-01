from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_operator_list_keyboard(count: int) -> InlineKeyboardMarkup:
    """
    Повертає клавіатуру з динамічними числовими кнопками та двома фіксованими:
    - ➕ Додати оператора
    - 🔙 Назад до панелі

    :param count: Кількість числових кнопок
    :return: InlineKeyboardMarkup
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Додавання числових кнопок по 4 в ряд
    row = []
    for i in range(1, count + 1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=str(i)))
        if len(row) == 4:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)

    # Додавання постійних кнопок
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="➕ Додати оператора",
            callback_data="add_operator"
        )
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="🔙 Назад до панелі",
            callback_data="admin_panel"
        )
    ])

    return keyboard

def get_servers_ip_list_keyboard(server_ips: list, back_button_callback_data: str = None, back_button_text:str=None) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Додавання числових кнопок по 4 в ряд
    row = []
    for ip in server_ips:
        row.append(InlineKeyboardButton(text=ip, callback_data=ip))
        keyboard.inline_keyboard.append(row)
        row = []

    # Додавання постійних кнопок
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="➕ Додати сервер",
            callback_data="add_server"
        )
    ])
    if back_button_callback_data is not None:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=back_button_text,
                callback_data=back_button_callback_data
            )
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="❌ Скасувати",
            callback_data="admin_panel"
        )
    ])

    return keyboard


def get_confirm_add_operator_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Додати", callback_data="confirm_add_operator"),
            InlineKeyboardButton(text="✏️ Редагувати", callback_data="edit_add_operator")
        ],
        [
            InlineKeyboardButton(text="❌ Скасувати", callback_data="add_proxies")
        ]
    ])


def get_protocols_list_keyboard(protocols: list) -> InlineKeyboardMarkup:
    """
    Повертає клавіатуру з кнопками з назвами протоколів та кнопкою "Назад".

    :param protocols: список словників з протоколами (мають ключ 'id' і 'value')
    :return: InlineKeyboardMarkup
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    row = []
    for protocol in protocols:
        btn = InlineKeyboardButton(
            text=protocol["value"],
            callback_data=str(protocol["id"])
        )
        keyboard.inline_keyboard.append([btn])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="🔙 Назад до операторів",
            callback_data="add_proxies"
        )
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="❌ Скасувати",
            callback_data="admin_panel"
        )
    ])

    return keyboard
