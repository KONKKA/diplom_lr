import asyncio
import logging

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup

from app.database.requests.get_data import (get_catalog_item_by_id, get_user_balance_by_tg_id,
                                            get_first_available_proxy_by_type_id,
                                            get_first_available_port_id_by_server_id,
                                            get_current_proxies_price_per_week, get_task_status)
from app.database.requests.save_data import update_proxy_status, create_proxy_rental, decrease_user_balance, \
        update_port_status
from app.database.requests.task_handler import add_task_to_queue, wait_for_task_completion
from app.keyboards.catalog import get_back_catalog_keyboard
from app.keyboards.universal_keyboards import get_confirm_or_cancel_keyboard
from app.menu.menu import send_catalog_page, send_main_menu
from app.utils.login_data_generator import generate_3proxy_credentials
from app.utils.text_generator import get_catalog_item_text

router = Router()


class CatalogStates(StatesGroup):
        waiting_for_product_choice: State = State()
        waiting_for_term_input: State = State()
        is_term_inputting: State = State()
        waiting_for_confirm: State = State()


@router.callback_query(~StateFilter(CatalogStates.is_term_inputting),F.data == "proxy_catalog")
async def handle_catalog_list(callback: CallbackQuery, state: FSMContext):
        await state.set_state(CatalogStates.waiting_for_product_choice)
        await send_catalog_page(callback)


@router.callback_query(CatalogStates.waiting_for_product_choice, F.data.regexp(r'^\d+$'))
async def handle_catalog_product_choice(callback: CallbackQuery, state: FSMContext):
        catalog_id = int(callback.data)
        catalog = await get_catalog_item_by_id(catalog_id)
        user_balance = await get_user_balance_by_tg_id(callback.from_user.id)
        await state.update_data(catalog = catalog)
        await state.update_data(user_balance = user_balance)

        text = get_catalog_item_text(catalog)
        text += (
                "\n\n"
                "⏳ <b>Термін оренди:</b>\n"
                "▸ Введіть кількість тижнів\n"
                "▸ <i>Або <code>0</code> для відміни</i>"
        )

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_catalog_keyboard())
        await callback.answer()
        await state.set_state(CatalogStates.waiting_for_term_input)


@router.message(CatalogStates.is_term_inputting)
@router.message(CatalogStates.waiting_for_term_input)
async def handle_price_input(message: Message, state: FSMContext):
        await state.set_state(CatalogStates.is_term_inputting)

        try:
                term = int(message.text)
                if term < 0:
                        raise ValueError
                if term == 0:
                        await state.set_state(CatalogStates.waiting_for_product_choice)
                        await send_catalog_page(message)
                        return

        except ValueError:
                error_text = (
                        "⚠️ <b>Некоректний ввід</b>\n\n"
                        "⌛ Введіть кількість <b>тижнів</b> (ціле число > 0)\n"
                        "✖️ Або <code>0</code> для виходу в меню\n\n"
                        "Приклад: <code>2</code> - оренда на 2 тижні"
                )
                await message.answer(text=error_text, parse_mode="HTML")
                return

        data = await state.get_data()
        catalog = data.get("catalog")

        price = catalog.get("price_per_week") * term
        await state.update_data(term = term)

        if price > data.get("user_balance"):
                error_text = (
                        "⚠️ <b>Недостатньо коштів на балансі</b>\n\n"
                        f"💳 <b>Ваш баланс:</b> <code>{data.get('user_balance')}</code>\n"
                        f"💲 <b>Вартість оренди:</b> <code>{price}</code>\n\n"
                        "ℹ️ Оберіть менший термін оренди:\n"
                        "✖️ Або <code>0</code> для виходу в меню"
                )
                await message.answer(
                        text=error_text,
                        parse_mode="HTML"
                )
                return

        await state.set_state(CatalogStates.waiting_for_confirm)

        text = get_catalog_item_text(catalog)
        text += (
                "\n📝 <b>Деталі оренди</b>\n"
                "════════════════════════\n"
                f"⏳ <b>Термін:</b> <code>{term}</code> тижні(в)\n"
                f"💳 <b>Вартість:</b> <code>{price}</code>\n\n"
                "<b>Підтвердіть оренду:</b>"
        )
        keyboard= get_confirm_or_cancel_keyboard("confirm_purchase","proxy_catalog")

        await message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(CatalogStates.waiting_for_confirm, F.data == "confirm_purchase")
async def handle_confirm_purchase(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(" ⏳ Зачекайте...")
    try:
        data = await state.get_data()
        catalog = data.get("catalog")
        term = data.get("term")

        if not catalog or not term:
            raise RuntimeError("❌ Дані про товар втрачено. Спробуйте ще раз.")

        proxy_type_id = catalog.get("proxy_type_id")
        proxy = await get_first_available_proxy_by_type_id(proxy_type_id)
        if not proxy:
            raise RuntimeError("😔 Вільних проксі цього типу зараз немає.")

        server_id = proxy.get("server_id")
        port_id = await get_first_available_port_id_by_server_id(server_id)
        if not port_id:
            raise RuntimeError("😔 Вільних проксі цього типу зараз немає.")

        current_price_per_week = await get_current_proxies_price_per_week(catalog.get("id"))
        if not current_price_per_week:
            raise RuntimeError("❌ Не вдалося отримати актуальну ціну. Спробуйте ще раз.")

        total_price = current_price_per_week * term
        user_balance = await get_user_balance_by_tg_id(callback.from_user.id)
        if user_balance is None:
            raise RuntimeError("🔍 Не вдалося отримати інформацію про ваш баланс.")
        if user_balance < total_price:
            raise RuntimeError(
                f"💰 Недостатньо коштів для покупки.\n\n"
                f"Ваш баланс: {user_balance:.2f}\n"
                f"Вартість оренди: {total_price:.2f}\n\n"
                f"Будь ласка, поповніть баланс."
            )

        login_data = await generate_3proxy_credentials()
        if not login_data:
            raise RuntimeError("🔑 Помилка при генерації облікових даних.")

        if not await decrease_user_balance(callback.from_user.id, total_price):
            raise RuntimeError("💳 Помилка при списанні коштів. Зв'яжіться з підтримкою.")

        proxy_id = proxy.get("id")
        rental = await create_proxy_rental(
            tg_id=callback.from_user.id,
            proxy_id=proxy_id,
            term=term,
            port_id=port_id,
            login=login_data.get("login"),
            password=login_data.get("password")
        )
        if not rental:
            raise RuntimeError("⏳ Помилка при створенні оренди. Зв'яжіться з підтримкою.")

        if not await update_proxy_status(proxy_id, "Rented"):
            raise RuntimeError("⚠️ Не вдалося забронювати проксі. Спробуйте ще раз.")

        if not await update_port_status(port_id, "Rented"):
            raise RuntimeError("⚠️ Не вдалося забронювати порт. Спробуйте ще раз.")

        task_id = await add_task_to_queue(
            proxy_id=proxy_id,
            port_id=port_id,
            login=login_data.get("login"),
            password=login_data.get("password")
        )

        if not task_id or not await wait_for_task_completion(task_id, timeout=5):
            raise RuntimeError(
"""
⏳ Час очікування вичерпано!

Не вдалося завершити обробку вашого запиту.
Можливі причини:
- Сервер тимчасово недоступний
- Перевищений час очікування відповіді

Що потрібно зробити:
1. Товар було успішно додано до <b>📊 Мої проксі</b>
2. Перевірте з'єднання з проксі
3. Якщо виникла проблема - зверніться до підтримки

📌 Ми вже працюємо над вирішенням цієї ситуації!
"""
            )


        await callback.message.edit_text(
            "🎉 Вітаємо з успішною покупкою!\n\n"
            f"Перейдіть в <b>📊 Мої проксі</b>\n", parse_mode="HTML"
        )
        await state.clear()
        await send_main_menu(callback.from_user.id, message=callback.message)

    except RuntimeError as user_error:
        await callback.message.edit_text(str(user_error), parse_mode="HTML")
        await state.set_state(CatalogStates.waiting_for_product_choice)
        await send_catalog_page(callback.message)

    except Exception as e:
        logging.exception(f"Unhandled error in handle_confirm_purchase: {e}")
        await callback.message.edit_text(
            "⚡️ Сталася неочікувана помилка. Ми вже працюємо над вирішенням.\n"
            "Будь ласка, спробуйте пізніше або зверніться до підтримки."
        )
        await state.set_state(CatalogStates.waiting_for_product_choice)
        await send_catalog_page(callback.message)






