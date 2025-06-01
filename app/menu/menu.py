from typing import Union

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from app.database.requests.get_data import get_server_ips_list, get_all_operators, get_all_protocols, \
    get_available_catalog, get_user_id_by_tg_id, get_user_proxies_list
from app.database.requests.user import get_user
from app.keyboards.admin.add_proxies import get_servers_ip_list_keyboard, get_operator_list_keyboard, \
    get_protocols_list_keyboard
from app.keyboards.admin.panel import get_admin_panel_keyboard
from app.keyboards.admin.proxy_settings import build_pagination_keyboard
from app.keyboards.catalog import get_catalog_number_keyboard
from app.keyboards.menu import get_menu_buttons
from app.utils.admin_utils import is_admin
from app.utils.text_generator import get_operators_catalog_text, get_profile_text, get_proxy_catalog_text, \
    get_proxies_user_list_text


async def send_server_choice_menu(
        target: Union[Message, CallbackQuery],
        back_button_callback_data: str = "back_to_protocols",
        back_button_text: str = "🔙 Назад до протоколів"):
    """
    Sends a message or edits a message to display the server choice menu.

    Args:
        target (Union[Message, CallbackQuery]): The target to send or edit the message.
        back_button_callback_data (str, optional): Callback data for the back button. Defaults to "back_to_protocols".
        back_button_text (str, optional): Text for the back button. Defaults to "🔙 Назад до протоколів".
    """
    server_ips = await get_server_ips_list()

    text = (
        "Оберіть необхідний сервер\n\n"
    )
    keyboard = get_servers_ip_list_keyboard(server_ips, back_button_callback_data, back_button_text)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await target.answer()
    elif isinstance(target, Message):
        await target.answer(text, parse_mode="HTML", reply_markup=keyboard)


async def send_admin_panel(target, user_id: int, first_name: str):
    """
    Sends or edits a message to show the admin panel.

    Args:
        target (Union[Message, CallbackQuery]): The target to send or edit the message.
        user_id (int): Telegram user ID of the admin.
        first_name (str): First name of the admin user.
    """
    text = (
        "🛡️ Адмін Панель\n"
        "════════════════════════\n\n"
        f"Вітаємо, <b>{first_name}</b>!\n\n"
        f"📌 ID: <code>{user_id}</code>\n"
        "⚙️ Роль: Адміністратор\n\n"
        "Обирайте дію з меню нижче ⬇️"
    )

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_panel_keyboard())
        await target.answer()
    elif isinstance(target, Message):
        await target.answer(text, parse_mode="HTML", reply_markup=get_admin_panel_keyboard())


async def send_operators_choice_menu(target: Union[Message, CallbackQuery]):
    """
    Sends or edits a message to display a list of available operators for selection.

    Args:
        target (Union[Message, CallbackQuery]): The target to send or edit the message.
    """
    operators = await get_all_operators()
    text = get_operators_catalog_text(operators)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_operator_list_keyboard(len(operators))
        )
        await target.answer()
    elif isinstance(target, Message):
        await target.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_operator_list_keyboard(len(operators))
        )


async def send_protocols_choice_menu(target: Union[Message, CallbackQuery]):
    """
    Sends or edits a message to display a list of available protocols for selection.

    Args:
        target (Union[Message, CallbackQuery]): The target to send or edit the message.
    """
    protocols = await get_all_protocols()
    text = "Оберіть протокол:"
    keyboard = get_protocols_list_keyboard(protocols)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await target.answer()
    elif isinstance(target, Message):
        await target.answer(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


async def send_main_menu(tg_id: int, is_callback: bool = False, message=None, callback: CallbackQuery = None):
    """
    Sends or edits the main user profile menu with user's information.

    Args:
        tg_id (int): Telegram user ID.
        is_callback (bool, optional): Whether the call comes from a callback query. Defaults to False.
        message (Message, optional): Message object if sending new message. Defaults to None.
        callback (CallbackQuery, optional): CallbackQuery object if editing existing message. Defaults to None.
    """
    user = await get_user(tg_id)
    text = get_profile_text(user)
    keyboard = InlineKeyboardMarkup(inline_keyboard=get_menu_buttons(is_admin(tg_id)))

    if is_callback:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()
    else:
        await message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


async def send_catalog_page(target: Union[Message, CallbackQuery]):
    """
    Sends or edits a message displaying the available proxy catalog with selection options.

    Args:
        target (Union[Message, CallbackQuery]): The target to send or edit the message.
    """
    available_catalog = await get_available_catalog()

    text = get_proxy_catalog_text(available_catalog)
    if available_catalog:
        text += "\nВиберіть потрібний проксі для оренди."
    keyboard = get_catalog_number_keyboard(available_catalog)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await target.answer()
    elif isinstance(target, Message):
        await target.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


async def send_my_proxies_page(target: Union[Message, CallbackQuery]):
    """
    Sends or edits a message showing the list of proxies rented by the user with pagination.

    Args:
        target (Union[Message, CallbackQuery]): The target to send or edit the message.
    """
    user_id = await get_user_id_by_tg_id(target.from_user.id)
    user_proxies = await get_user_proxies_list(user_id)
    text, total_pages = get_proxies_user_list_text(user_proxies)
    keyboard = build_pagination_keyboard(page=1, total_pages=total_pages, back_callback_data="back_to_menu")

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await target.answer()
    elif isinstance(target, Message):
        await target.answer(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )




