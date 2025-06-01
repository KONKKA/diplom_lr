from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.filters.isAdmin import IsAdmin
from app.menu.menu import send_admin_panel

router = Router()


@router.callback_query(IsAdmin(), F.data == "admin_panel")
async def show_admin_panel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await send_admin_panel(callback, callback.from_user.id, callback.from_user.first_name)