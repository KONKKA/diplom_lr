import logging

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup

from app.database.requests.user import update_user
from app.menu.menu import send_main_menu
from app.keyboards.menu import get_support_keyboard, get_back_reply_button
from app.keyboards.registration import get_contact_reply_button

router = Router()

class EditSettingsStates(StatesGroup):
    waiting_for_changes: State = State()


@router.callback_query(StateFilter(None), F.data == "profile_settings")
async def profile_settings_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditSettingsStates.waiting_for_changes)

    buttons = get_contact_reply_button() + get_back_reply_button()
    await callback.message.edit_text(
        "Якщо ваші контактні дані в Телеграм змінилися",
        reply_markup=None
    )
    keyboard = ReplyKeyboardMarkup(keyboard=buttons,
                                   resize_keyboard=True,
                                   one_time_keyboard=True)
    await callback.message.answer(
        ("Натисніть кнопку нижче:"),
        reply_markup=keyboard
    )
    print(state.get_state())
    await callback.answer()

@router.message(EditSettingsStates.waiting_for_changes, F.contact)
async def process_contact_handler(message: Message, state: FSMContext, bot: Bot):
    contact = message.contact
    logging.info(f"Contact: {contact}")

    try:
        await update_user(contact.user_id, contact.first_name, contact.last_name, contact.phone_number, message.from_user.username)
        await message.answer(
            ("✅ Ваші дані успішно оновлено!"),
            reply_markup=ReplyKeyboardRemove()
        )
        await send_main_menu(tg_id=message.from_user.id, message=message)

        try:
            await bot.delete_message(message.chat.id, message.message_id - 1)
            await bot.delete_message(message.chat.id, message.message_id - 2)
        except:
            pass

    except ValueError as e:
        await message.answer(
            "Помилка",
            reply_markup=ReplyKeyboardRemove()
        )

        await message.answer(
            f"❗ {str(e)}",
            reply_markup=get_support_keyboard()
        )
    await state.clear()