from aiogram import F, Bot, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from app.handlers.profile_settings import EditSettingsStates
from app.keyboards.registration import get_registration_keyboard
from app.database.requests.user import user_exists
from app.menu.menu import send_main_menu
from config import BOT_NAME

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext,bot:Bot):
    await state.clear()

    for msg_id in [message.message_id - 1, message.message_id - 2]:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception:
            continue

    # Привітання
    welcome_text = (
        f"🌟 <b>Вітаємо в {BOT_NAME}, {message.from_user.first_name}!</b> 🌟\n\n"
        "🛡️ Ваш надійний постачальник якісних проксі-серверів\n\n"
        "🎁 <b>Привітальний бонус: +50</b>🪙 за реєстрацію!\n\n"
    )
    await message.answer(welcome_text, parse_mode="HTML")

    # Перевірка реєстрації
    if not await user_exists(message.from_user.id):
        await message.answer(
            f"Для доступу до {BOT_NAME} вам необхідно завершити реєстрацію",
            reply_markup=get_registration_keyboard()
        )
    else:
        await send_main_menu(tg_id=message.from_user.id, message=message)


@router.message(EditSettingsStates.waiting_for_changes, F.text == "Повернутися в меню")
async def back_from_settings_handler(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    await message.answer("Головне меню", reply_markup=ReplyKeyboardRemove())

    await send_main_menu(tg_id=message.from_user.id, message=message)

    # Спроба видалити попередні повідомлення
    for msg_id in [message.message_id - 1, message.message_id - 2]:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception:
            continue


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await send_main_menu(tg_id=callback.from_user.id, is_callback=True, callback=callback)
