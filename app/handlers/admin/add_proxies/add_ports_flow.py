import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from sqlalchemy import CreateEnginePlugin

from app.database.requests.save_data import save_port_list
from app.filters.isAdmin import IsAdmin
from app.keyboards.universal_keyboards import get_confirm_or_cancel_keyboard, get_back_keyboard
from app.menu.menu import send_server_choice_menu, send_admin_panel

router = Router()

class AddPortsState(StatesGroup):
    waiting_for_server_ip_choice = State()
    waiting_for_ports_input_start = State()
    waiting_for_correct_ports_input = State()
    waiting_for_confirm_data = State()

@router.callback_query(IsAdmin(), F.data == "add_ports")
async def handle_choice_operators(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.update_data(is_port_choice = True)
    await send_server_choice_menu(callback, None)
    await state.set_state(AddPortsState.waiting_for_server_ip_choice)


@router.callback_query(IsAdmin(), AddPortsState.waiting_for_server_ip_choice, F.data.regexp(r'^(\d{1,3}\.){3}\d{1,3}$'))
async def handle_start_adding_ports(callback: CallbackQuery, state: FSMContext):
    await state.update_data(server_ip=callback.data)
    await callback.message.edit_text(
        "⚠️ Введіть відкриті порти сервера:\n"
        "Формат: через пробіл, тире, кому або з нового рядку\n"
        "Приклад: `8080 9090`/`8080, 9090`/'8001-8090'",
        reply_markup = get_back_keyboard("back_to_server_choice")
    )
    await state.set_state(AddPortsState.waiting_for_ports_input_start)


@router.message(IsAdmin(), AddPortsState.waiting_for_correct_ports_input)
@router.message(IsAdmin(), AddPortsState.waiting_for_ports_input_start)
async def handle_ports_input(message: Message, state: FSMContext):
    await state.set_state(AddPortsState.waiting_for_correct_ports_input)
    try:
        raw_ports = message.text.strip()
        normalized = raw_ports.replace(',', ' ').replace('\n', ' ')

        # Розбиваємо на окремі порти та діапазони
        port_list = []
        for item in normalized.split():
            item = item.strip()
            if not item:
                continue

            # Обробка діапазону портів (формат: X-Y)
            if '-' in item:
                try:
                    start, end = map(int, item.split('-'))
                    if start > end:
                        start, end = end, start  # Автоматично виправляємо порядок

                    if not (1 <= start <= 65535 and 1 <= end <= 65535):
                        await message.reply(f"⛔ Діапазон {item} містить невалідні порти (має бути 1-65535)")
                        return

                    port_list.extend(range(start, end + 1))
                except ValueError:
                    await message.reply(f"❌ Невірний формат діапазону: {item}")
                    return
            else:
                # Обробка одиночного порту
                try:
                    port = int(item)
                    if 1 <= port <= 65535:
                        port_list.append(port)
                    else:
                        await message.reply(f"⛔ Порт {port} не валідний (має бути 1-65535)")
                        return
                except ValueError:
                    await message.reply(f"❌ Невірний формат порту: {item}")
                    return

        if not port_list:
            await message.reply("❌ Не знайдено жодного валідного порту")
            return

        # Видаляємо дублікати та сортуємо
        port_list = sorted(list(set(port_list)))

        # Перевірка кількості портів
        if len(port_list) > 100:
            await message.reply("⚠️ Забагато портів (максимум 100 за раз)")
            return

        # Оновлюємо стан
        await state.update_data(ports=port_list)

        # Підтвердження
        if len(port_list) <= 10:
            ports_str = ', '.join(map(str, port_list))
        else:
            ports_str = f"{port_list[0]}-{port_list[-1]} ({len(port_list)} портів)"

        await message.answer(
            f"📋 Отримано порти:\n{ports_str}\n\nВсе вірно?",
            reply_markup=get_confirm_or_cancel_keyboard("confirm_ports_adding", "admin_panel"))
        await state.set_state(AddPortsState.waiting_for_confirm_data)

    except Exception as e:
        logging.error(f"Помилка обробки портів: {e}")
        await message.answer("⚠️ Сталася помилка. Спробуйте ще раз")
        await send_admin_panel(message, message.from_user.id, message.from_user.first_name)
        await state.clear()

@router.callback_query(IsAdmin(),AddPortsState.waiting_for_confirm_data, F.data == "confirm_ports_adding")
async def handle_confirm_ports_adding(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ports = data['ports']
    server_ip = data['server_ip']
    from app.database.requests.get_data import get_server_id_by_ip
    server_id = await get_server_id_by_ip(server_ip)
    if server_id is not None:
        success_text = await save_port_list(ports, server_id)
        await callback.message.edit_text(success_text)
    else:
        await callback.message.edit_text("❌ Сервер з вказаною адресою відсутній")
    await send_admin_panel(callback.message, callback.from_user.id, callback.from_user.first_name)
    await state.clear()

