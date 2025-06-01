from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message

from app.database.requests.get_data import get_all_catalog
from app.database.requests.edit_prices import update_proxy_price
from app.filters.isAdmin import IsAdmin
from app.keyboards.catalog import get_catalog_number_keyboard
from app.utils.text_generator import get_proxy_catalog_text

router = Router()

class EditPricesStates(StatesGroup):
    waiting_for_products_choice = State()
    waiting_for_price_input = State()

async def send_edit_proxies_price_menu(event: CallbackQuery | Message, state: FSMContext):
    catalog = await get_all_catalog()
    text = get_proxy_catalog_text(catalog)
    text += "\nОберіть проксі для редагування ціни:"

    markup = get_catalog_number_keyboard(catalog, menu_callback_data="admin_panel")

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
        await event.answer()
    else:  # event is Message
        await event.answer(text, parse_mode="HTML", reply_markup=markup)

    await state.set_state(EditPricesStates.waiting_for_products_choice)



@router.callback_query(IsAdmin(),F.data == "edit_prices")
async def handle_load_edit_prices(callback: CallbackQuery, state: FSMContext):
    await send_edit_proxies_price_menu(callback, state)


@router.callback_query(IsAdmin(), EditPricesStates.waiting_for_products_choice, F.data.regexp(r'^\d+$'))
async def handle_click_numeric_button(callback: CallbackQuery, state: FSMContext):
    catalog_id = int(callback.data)

    await state.update_data(catalog_id=catalog_id)

    await callback.message.edit_text("✏️ Введіть нову ціну для обраного типу проксі:")
    await state.set_state(EditPricesStates.waiting_for_price_input)
    await callback.answer()

@router.message(IsAdmin(), EditPricesStates.waiting_for_price_input)
async def handle_price_input(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❗ Введіть коректне ціле число, що більше або дорівнює 0.")
        return

    data = await state.get_data()
    catalog_id = data.get("catalog_id")

    success = await update_proxy_price(catalog_id, price)

    if success:
        await message.answer(f"✔️ Ціну <b>{price}</b> збережено.", parse_mode="HTML")
    else:
        await message.answer("⚠️ Сталася помилка під час збереження ціни.")

    await state.clear()
    await send_edit_proxies_price_menu(message, state)
