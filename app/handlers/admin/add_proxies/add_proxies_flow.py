from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message

from app.database.requests.save_data import save_proxies_from_fsm
from app.database.requests.get_data import get_operator_by_id, get_protocol_by_id
from app.filters.isAdmin import IsAdmin
from app.menu.menu import send_admin_panel, send_server_choice_menu, send_operators_choice_menu, \
    send_protocols_choice_menu
from app.keyboards.universal_keyboards import get_confirm_or_cancel_keyboard
from app.utils.constants import IPV4_PATTERN

router = Router()


class AddProxiesState(StatesGroup):
    waiting_for_operators_choice = State()
    waiting_for_protocol_choice = State()
    waiting_for_server_ip_choice = State()
    waiting_for_internal_ips_input = State()
    waiting_for_pools_choice = State()
    waiting_for_data_confirmation = State()


@router.callback_query(IsAdmin(), F.data == "add_proxies")
async def handle_choice_operators(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AddProxiesState.waiting_for_operators_choice)
    await send_operators_choice_menu(callback)


@router.callback_query(IsAdmin(), AddProxiesState.waiting_for_operators_choice, F.data.regexp(r'^\d+$'))
async def handle_choice_protocol(callback: CallbackQuery, state: FSMContext):
    await state.update_data(operator_id=int(callback.data))
    await send_protocols_choice_menu(callback)
    await state.set_state(AddProxiesState.waiting_for_protocol_choice)
    await callback.answer()



@router.callback_query(IsAdmin(), AddProxiesState.waiting_for_protocol_choice, F.data.regexp(r'^\d+$'))
async def handle_choice_server(callback: CallbackQuery, state: FSMContext):
    await state.update_data(protocol_id=int(callback.data))
    await send_server_choice_menu(callback)
    await state.set_state(AddProxiesState.waiting_for_server_ip_choice)
    await callback.answer()

@router.callback_query(IsAdmin(), AddProxiesState.waiting_for_server_ip_choice, F.data.regexp(r'^(\d{1,3}\.){3}\d{1,3}$'))
async def handle_choice_server_process(callback: CallbackQuery, state: FSMContext):
    await state.update_data(server_ip=callback.data)
    await callback.message.edit_text("Введіть внутрішні IP-адреси у форматі xxx.xxx.xxx.xxx через кому:")
    await state.set_state(AddProxiesState.waiting_for_internal_ips_input)

@router.message(IsAdmin(),AddProxiesState.waiting_for_internal_ips_input)
async def handle_internal_ips_input(message: Message, state: FSMContext):
    raw_input = message.text.strip()

    # Підтримка вводу через кому або новий рядок
    ip_candidates = [ip.strip() for ip in raw_input.replace(',', '\n').split('\n') if ip.strip()]

    if not ip_candidates:
        await message.answer("❌ Ви не ввели жодної IP-адреси.")
        return

    valid_ips = []
    for ip in ip_candidates:
        if not IPV4_PATTERN.match(ip):
            await message.answer(
                f"❌ Неправильний формат IP: <code>{ip}</code>\nВведіть усі адреси у форматі xxx.xxx.xxx.xxx.",
                parse_mode="HTML")
            return

        octets = ip.split('.')
        for o in octets:
            if not (0 <= int(o) <= 255):
                await message.answer(f"❌ IP-адреса <code>{ip}</code> містить октет поза діапазоном 0–255.",
                                     parse_mode="HTML")
                return
            if len(o) > 1 and o.startswith('0'):
                await message.answer(f"❌ IP-адреса <code>{ip}</code> містить недопустимий ведучий нуль.",
                                     parse_mode="HTML")
                return

        valid_ips.append(ip)

    await state.update_data(internal_ips=valid_ips)
    await handle_confirm_enters_data(message,state)


async def handle_confirm_enters_data(message: Message, state: FSMContext):
    data = await state.get_data()

    # Отримуємо деталі для тексту
    operator = await get_operator_by_id(data["operator_id"])
    protocol = await get_protocol_by_id(data["protocol_id"])
    server_ip = data["server_ip"]
    internal_ips = data["internal_ips"]

    text = (
            "<b>Підтвердження введених даних:</b>\n\n"
            f"🌍 <b>Оператор:</b> {operator['name']} ({operator['country_code']})\n"
            f"🔌 <b>Протокол:</b> {protocol['value']}\n"
            f"🌐 <b>Зовнішній IP:</b> <code>{server_ip}</code>\n"
            f"🧩 <b>Внутрішні IP:</b>\n" +
            "".join(f"• <code>{ip}</code>\n" for ip in internal_ips)
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_confirm_or_cancel_keyboard("confirm_proxy_data","admin_panel")
    )
    await state.set_state(AddProxiesState.waiting_for_data_confirmation)



@router.callback_query(
    IsAdmin(),
    AddProxiesState.waiting_for_data_confirmation,
    F.data == "confirm_proxy_data"
)
async def handle_save_data(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    try:
        success_text = await save_proxies_from_fsm(data)
        await callback.message.edit_text(success_text)
    except Exception as e:
        await callback.message.edit_text(f"❌ Помилка при збереженні проксі: {str(e)}")

    await state.clear()
    await send_admin_panel(callback.message,callback.from_user.id, callback.from_user.first_name)
    await callback.answer()

