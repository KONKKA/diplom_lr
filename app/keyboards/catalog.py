from typing import List, Dict

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_catalog_number_keyboard(catalog_list: List[Dict[str, str]], menu_callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    """
    Генерує Inline-клавіатуру з числом кнопок, що відповідає параметру count.
    Кнопки розташовуються по 4 в ряд. Текст і callback_data кожної кнопки — це її номер.

    :param count: Кількість кнопок
    :return: InlineKeyboardMarkup з кнопками від 1 до count
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    row = []
    for item in catalog_list:
        row.append(InlineKeyboardButton(text=str(item['catalog_id']), callback_data=str(item['catalog_id'])))
        if len(row) == 4:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="🔙 Повернутися",
            callback_data=menu_callback_data
        )
    ])

    return keyboard

def get_back_catalog_keyboard() -> InlineKeyboardMarkup:
     return InlineKeyboardMarkup(
             inline_keyboard=[[
                InlineKeyboardButton(
                    text="🔙 Повернутися",
                    callback_data="proxy_catalog"
                )
         ]]
     )

