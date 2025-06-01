from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message

from app.database.requests.save_data import save_operator_to_db
from app.menu.menu import send_admin_panel
from app.keyboards.admin.add_proxies import get_confirm_add_operator_keyboard


class AddOperatorState(StatesGroup):
    waiting_for_country_code = State()
    waiting_for_operator_name = State()
    confirm_data = State()

router = Router()

@router.callback_query(F.data == "add_operator")
async def start_add_operator(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🌍 Введіть <b>код країни</b> у форматі ISO 3166-1 alpha-2 (наприклад: <code>UA</code>):",
        parse_mode="HTML",
    )
    await state.set_state(AddOperatorState.waiting_for_country_code)
    await callback.answer()


@router.message(AddOperatorState.waiting_for_country_code)
async def process_country_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()

    if not code.isalpha() or len(code) != 2:
        await message.answer(
            "❌ Код країни має містити <b>2 латинські літери</b>. Спробуйте ще раз.",
            parse_mode="HTML",
        )
        return

    await state.update_data(country_code=code)
    await message.answer(
        "🏢 Тепер введіть <b>назву оператора</b> (до 20 символів):",
        parse_mode="HTML",
    )
    await state.set_state(AddOperatorState.waiting_for_operator_name)


@router.message(AddOperatorState.waiting_for_operator_name)
async def process_operator_name(message: Message, state: FSMContext):
    name = message.text.strip().upper()

    if len(name) > 20:
        await message.answer("❌ Назва оператора занадто довга. Введіть до 20 символів.")
        return

    await state.update_data(operator_name=name)
    data = await state.get_data()

    country_code = data["country_code"]
    operator_name = data["operator_name"]

    await message.answer(
        f"🔎 Ви ввели:\n\n"
        f"🌍 Країна: <code>{country_code}</code>\n"
        f"🏢 Оператор: <b>{operator_name}</b>\n\n"
        f"Підтвердьте дію:",
        reply_markup=get_confirm_add_operator_keyboard(),
        parse_mode="HTML"
    )

    await state.set_state(AddOperatorState.confirm_data)


@router.callback_query(F.data == "edit_add_operator")
async def edit_add_operator(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔁 Добре, почнемо заново.\n\n🌍 Введіть <b>код країни</b> у форматі ISO 3166-1 alpha-2:",
        parse_mode="HTML",
        reply_markup = None
    )
    await state.set_state(AddOperatorState.waiting_for_country_code)
    await callback.answer()


@router.callback_query(F.data == "confirm_add_operator")
async def confirm_add_operator(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    country_code = data["country_code"]
    operator_name = data["operator_name"]

    if await save_operator_to_db(country_code, operator_name):
        await callback.message.edit_text(
            f"✅ Оператор <b>{operator_name}</b> <code>{country_code}</code> успішно доданий!",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"❌ Оператор <b>{operator_name}</b> <code>{country_code}</code> вже існує!",
            parse_mode="HTML")
    await send_admin_panel(callback.message, callback.from_user.id, callback.from_user.first_name)
    await callback.answer()
