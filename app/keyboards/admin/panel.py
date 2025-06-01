from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛠️ Додати проксі",
                    callback_data="add_proxies"
                ),
                InlineKeyboardButton(
                    text="🔌 Додати порти",
                    callback_data="add_ports"
                ),

            ],
            [
                InlineKeyboardButton(
                    text="📋 Список проксі",
                    callback_data="proxies_list"
                ),
                InlineKeyboardButton(
                    text="💲 Змінити ціни",
                    callback_data="edit_prices"
                )

            ],
            [
                InlineKeyboardButton(
                    text="👥 Користувачі",
                    callback_data="users_list"
                ),
                InlineKeyboardButton(
                    text="📅 Черга задач",
                    callback_data="task_queue"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Повернутися",
                    callback_data="back_to_menu"
                )
            ]
        ]
    )

def get_task_queue_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Завершені",
                    callback_data="done_tasks_queue"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👥 В черзі",
                    callback_data="current_tasks_queue"
                )

            ],
            [
                InlineKeyboardButton(
                    text="🚨 З помилками",
                    callback_data="error_tasks_queue"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Повернутися",
                    callback_data="admin_panel"
                )
            ]
        ]
    )

