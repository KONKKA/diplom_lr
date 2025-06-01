from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from app.database.requests.save_data import save_server_ip
from app.filters.isAdmin import IsAdmin
from app.handlers.admin.add_proxies.add_ports_flow import AddPortsState
from app.handlers.admin.add_proxies.add_proxies_flow import AddProxiesState
from app.utils.constants import IPV4_PATTERN
from app.handlers.universal import send_confirmation_request_panel
from app.keyboards.universal_keyboards import get_back_keyboard
from app.menu.menu import send_server_choice_menu, send_protocols_choice_menu

router = Router()

class AddServerState(StatesGroup):
    waiting_for_server_ip_input = State()
    waiting_for_correct_ip_input = State()
    waiting_for_server_ip_confirmation = State()

@router.callback_query(IsAdmin(), AddPortsState.waiting_for_ports_input_start, F.data == "back_to_server_choice")
@router.callback_query(IsAdmin(),AddServerState.waiting_for_server_ip_confirmation, F.data =="back_to_server_choice")
@router.callback_query(IsAdmin(),AddServerState.waiting_for_server_ip_input, F.data =="back_to_server_choice")
async def handle_back_to_servers_choice_menu(callback: CallbackQuery,state: FSMContext):
    data = await state.get_data()
    is_port_choice = data.get("is_port_choice")
    if is_port_choice:
        await send_server_choice_menu(callback, None)
        await state.clear()
        await state.set_state(AddPortsState.waiting_for_server_ip_choice)
    else:
        await send_server_choice_menu(callback)
        await state.set_state(AddProxiesState.waiting_for_server_ip_choice)
    await callback.answer()

@router.callback_query(IsAdmin(),AddProxiesState.waiting_for_server_ip_choice, F.data =="back_to_protocols")
@router.callback_query(IsAdmin(),AddServerState.waiting_for_server_ip_input, F.data =="back_to_protocols")
async def handle_back_to_protocols_choice_menu(callback: CallbackQuery, state: FSMContext):
    await send_protocols_choice_menu(callback)
    await state.set_state(AddProxiesState.waiting_for_protocol_choice)
    await callback.answer()

@router.callback_query(IsAdmin(), F.data=="add_server")
async def handle_show_add_server_menu(callback: CallbackQuery, state: FSMContext):
    text = "⚠️ Введіть IP адресу сервера у форматі xxx.xxx.xxx.xxx (наприклад, 192.168.1.1):"
    keyboard = get_back_keyboard('back_to_server_choice')
    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(AddServerState.waiting_for_server_ip_input)
    await callback.answer()

@router.message(IsAdmin(),AddServerState.waiting_for_server_ip_input)
@router.message(IsAdmin(),AddServerState.waiting_for_correct_ip_input)
async def handle_server_ip_input(message: Message, state: FSMContext):
    await state.set_state(AddServerState.waiting_for_correct_ip_input)
    server_ip = message.text.strip()

    # Перевірка формату IP (проста, перевіряє структуру xxx.xxx.xxx.xxx)
    if not IPV4_PATTERN.match(server_ip):
        await message.answer("❌ Неправильний формат IP. Будь ласка, введіть IP у форматі xxx.xxx.xxx.xxx (наприклад, 192.168.1.1).")
        return

    # Додаткова перевірка, щоб кожен октет був від 0 до 255
    octets = server_ip.split('.')

    for o in octets:
        if not (0 <= int(o) <= 255):
            await message.answer("❌ Кожен октет IP має бути в діапазоні від 0 до 255. Спробуйте ще раз.")
            return
        # Перевірка ведучих нулів (октет не повинен починатися з 0, якщо це не "0")
        if len(o) > 1 and o.startswith('0'):
            await message.answer(
                "❌ Октети не повинні містити ведучі нулі. Наприклад, '192.168.1.1', а не '192.168.001.01'. Спробуйте ще раз.")
            return

    await state.update_data(new_server_ip=server_ip)
    await state.set_state(AddServerState.waiting_for_server_ip_confirmation)

    text = f"❓ Додати новий сервер <code>{server_ip}</code>?"
    await send_confirmation_request_panel(
        message,
        text,
        "confirm_server_data",
        "back_to_server_choice"
    )

@router.callback_query(IsAdmin(), AddServerState.waiting_for_server_ip_confirmation, F.data == "confirm_server_data")
async def handle_save_server_data(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    server_ip = data.get("new_server_ip")
    data.pop("new_server_ip", None),
    is_port_choice = data.get("is_port_choice")
    await state.set_data(data)

    if await save_server_ip(server_ip):
        await callback.message.edit_text(f"✅ Сервер <code>{server_ip}</code> збережено\n\n", parse_mode="HTML")
    else:
        await callback.message.edit_text(f"❌ Сервер <code>{server_ip}</code> вже існує\n\n", parse_mode="HTML")
    if is_port_choice:
        await send_server_choice_menu(callback.message, None)
        await state.clear()
        await state.set_state(AddPortsState.waiting_for_server_ip_choice)
    else:
        await state.set_state(AddProxiesState.waiting_for_server_ip_choice)
        await send_server_choice_menu(callback.message)

