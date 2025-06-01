import logging

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, InlineKeyboardMarkup, \
    ReplyMarkupUnion
from app.database.requests.user import add_user, get_user
from app.keyboards.menu import get_support_keyboard, get_menu_buttons

from app.keyboards.registration import (
    get_accept_terms_button, get_contact_reply_button
)
from app.utils.admin_utils import is_admin
from app.utils.text_generator import get_profile_text

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_accept_terms: State = State()

# Старт реєстрації
@router.callback_query(F.data == "registration")
async def register_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RegistrationStates.waiting_for_accept_terms)
    await callback.message.edit_text(
        "📝 Ознайомтесь з угодою використання:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=get_accept_terms_button())
    )


# Після підтвердження угоди
@router.callback_query(RegistrationStates.waiting_for_accept_terms, F.data == "accept_terms")
async def accept_terms_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        ("Дякуємо за підтвердження угоди!\n\n"
          "Для завершення реєстрації поділіться своїм контактом:"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=get_contact_reply_button(),
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await callback.answer()


# Обробка отриманого контакту
@router.message(StateFilter(None), F.contact)
async def process_contact(message: Message, state: FSMContext):
    contact = message.contact
    logging.info(f"Contact: {contact}")

    try:
        await add_user(contact.user_id, contact.first_name, contact.last_name, contact.phone_number, message.from_user.username)
        await message.answer(
            ("✅ Реєстрація успішно завершена, {name}!\n"
             "Ваш номер: {phone}\n"
             "Ваш ID: {user_id}").format(
                name=contact.first_name,
                phone=contact.phone_number,
                user_id=contact.user_id
            ),
            reply_markup=ReplyKeyboardRemove()
        )
        user = await get_user(contact.user_id)
        text = get_profile_text(user)
        keyboard = InlineKeyboardMarkup(inline_keyboard=(get_menu_buttons(is_admin(message.from_user.id))))
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    except ValueError as e:
        await message.answer(
            "Помилка",
            reply_markup=ReplyKeyboardRemove()
        )

        await message.answer(
            f"❗ {str(e)}",
            reply_markup=get_support_keyboard()
        )

