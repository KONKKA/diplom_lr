from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from app.database.requests.get_data import get_all_proxies_info
from app.filters.isAdmin import IsAdmin
from app.keyboards.admin.proxy_settings import build_pagination_keyboard
from app.utils.text_generator import get_proxies_admin_list_text

router = Router()

class ProxySettingsStates(StatesGroup):
    waiting_for_proxy_choice = State()

@router.callback_query(IsAdmin(), F.data == "proxies_list")
async def handle_list_proxies(callback: CallbackQuery, state: FSMContext):
    proxies = await get_all_proxies_info()
    text, total_pages = get_proxies_admin_list_text(proxies)
    await state.set_state(ProxySettingsStates.waiting_for_proxy_choice)

    keyboard = build_pagination_keyboard(page=1, total_pages=total_pages)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)



@router.callback_query(IsAdmin(),ProxySettingsStates.waiting_for_proxy_choice, lambda c: c.data.startswith(("prev_", "next_")))
async def handle_pagination(callback: CallbackQuery, state: FSMContext):
    action, page = callback.data.split("_")
    page = int(page)

    proxies = await get_all_proxies_info()
    text, total_pages = get_proxies_admin_list_text(proxies, page=page)

    keyboard = build_pagination_keyboard(page=page, total_pages=total_pages)
    await callback.message.edit_text(text,parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()
