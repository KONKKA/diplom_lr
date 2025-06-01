from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery

from app.database.requests.get_data import get_user_id_by_tg_id, get_user_proxies_list
from app.keyboards.admin.proxy_settings import build_pagination_keyboard
from app.menu.menu import send_my_proxies_page
from app.utils.text_generator import get_proxies_user_list_text

router = Router()

class MyProxiesStates(StatesGroup):
    watching_proxies = State()

@router.callback_query(F.data == "my_proxies")
async def handle_my_proxies_page_load(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MyProxiesStates.watching_proxies)
    await send_my_proxies_page(callback)
    await callback.answer()

@router.callback_query(MyProxiesStates.watching_proxies,lambda c: c.data.startswith(("prev_", "next_")))
async def handle_pagination(callback: CallbackQuery):
    action, page = callback.data.split("_")
    page = int(page)

    user_id = await get_user_id_by_tg_id(callback.from_user.id)
    user_proxies = await get_user_proxies_list(user_id)
    text, total_pages = get_proxies_user_list_text(user_proxies, page=page)

    keyboard = build_pagination_keyboard(page=page, total_pages=total_pages, back_callback_data="back_to_menu")
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()



