import json
from datetime import datetime
from typing import List, Dict, Tuple

from app.database.models import ProxyTaskQueue


def get_profile_text(user_data) -> str:
    return (
        f"👤 <b>{user_data.first_name} {user_data.last_name or ''}</b>\n"
        "════════════════════════\n\n"
        f"📌 <b>ID:</b> <code>{user_data.tg_id}</code>\n"
        f"📱 <b>Телефон:</b> {user_data.phone_number}\n"
        f"💳 <b>Баланс:</b> {user_data.balance} монет\n\n"
        "<b>Доступні дії:</b>"
    )

def country_code_to_flag(code: str) -> str:
    return ''.join(chr(127397 + ord(char)) for char in code.upper())

def get_proxy_catalog_text(catalog_list) -> str:
    if not catalog_list:
        return "Каталог проксі наразі порожній."

    text = "📡 Каталог проксі\n\n"

    for item in catalog_list:
        flag = country_code_to_flag(item["country_code"])
        text += (
            f"<b>ID: {item['catalog_id']}\n</b>"
            f"<pre> 🛡️ Протокол: <b>{item['protocol']}</b>\n"
            f" {flag} Оператор: <b>{item['operator']} {item['country_code']}</b>\n"
            f" ⚡ Швидкість: <b>{item['speed']}</b>\n"
            f" 📦 В наявності: <b>{item['available_amount']}</b>\n"
            f" 💲 Ціна: <b>{item['price_per_week']}</b>/тиждень</pre>\n\n"
        )
    return text

def get_operators_catalog_text(operators_list) -> str:
    if not operators_list:
        return "Операторів немає в базі."

    text = "📡 Каталог операторів\n\n"

    for idx, operator in enumerate(operators_list, 1):
        flag = country_code_to_flag(operator["country_code"])
        text += (
            f"{idx}. {flag} Оператор: <b>{operator['name']} ({operator['country_code']})</b>\n"
        )

    text += "\nВиберіть оператора для подальших дій."

    return text


def get_proxies_admin_list_text(proxies: List[Dict], page: int = 1, per_page: int = 6) -> Tuple[str, int]:
    if not proxies:
        return "📡 Список проксі наразі порожній.", 0

    STATUS_ICONS = {
        "available": "🟢",
        "rented": "🟡",
        "unavailable": "🔴",
    }

    total_pages = (len(proxies) + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_proxies = proxies[start_idx:end_idx]

    header = (
        "🌐 <b>Список проксі</b>\n"
        f"Сторінка <b>{page}</b> з <b>{total_pages}</b>\n\n"
    )

    body = ""
    for proxy in page_proxies:
        flag = country_code_to_flag(proxy["country"])
        status_icon = STATUS_ICONS.get(proxy["status"].lower(), "⚪")

        body += (
            f"<pre>id: {proxy['id']}\n"
            f"server ip: {proxy['server_ip']}\n"
            f"internal IP: {(proxy['internal_ip'])}\n"
            f"operator: {proxy['operator']} ({proxy['country']})\n"
            f"protocol: {proxy['protocol']}\n"
            f"status: {proxy['status']} {status_icon}</pre>\n\n"
        )

    if len(proxies) >= per_page:
        body += "ℹ️ Використовуйте кнопки навігації для перегляду"

    return header + body, total_pages


def get_catalog_item_text(catalog_item) -> str:

        if not catalog_item:
            return "<b>Ви нічого не обрали</b>"

        flag = country_code_to_flag(catalog_item["country_code"])

        text = (
            f"🔀 <b>Ви обрали</b>\n"
            "<pre>"
            f"🛡️ <b>Протокол:</b> <code>{catalog_item['protocol']}</code>\n"
            f"{flag} <b>Оператор:</b> <code>{catalog_item['operator']} ({catalog_item['country_code']})</code>\n"
            f"📦 <b>В наявності:</b> <code>{catalog_item['available_amount']} шт.</code>\n"
            f"💲 <b>Ціна:</b> <code>{catalog_item['price_per_week']}/тиждень</code></pre>"
        )

        return text


def get_proxies_user_list_text(proxies: List[Dict], page: int = 1, per_page: int = 2) -> Tuple[str, int]:
    if not proxies:
        return "📡 Список проксі наразі порожній.", 0

    total_pages = (len(proxies) + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_proxies = proxies[start_idx:end_idx]

    text = "🌐 <b>Ваші проксі сервери</b>\n\n"

    for idx, proxy in enumerate(page_proxies, start_idx + 1):
        # Форматування дат
        purchase_date = proxy['purchase_date'].strftime("%d.%m.%Y %H:%M")
        expire_date = proxy['expire_date'].strftime("%d.%m.%Y %H:%M")

        # Розрахунок часу, що залишився
        time_left = proxy['expire_date'] - datetime.now()
        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes = remainder // 60
        time_left_str = f"{days} дн. {hours} год. {minutes} хв."

        # Формування посилання
        protocol = proxy['protocol'].upper()
        if protocol in ('SOCKS5'):
            connect_link = f"socks5://{proxy['login']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
        else:
            connect_link = f"http://{proxy['login']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
        flag = country_code_to_flag(proxy['country_code'])
        text += (
            f"🔹 <b>Проксі #{idx}</b>\n"
            f"<code>{proxy['ip']}:{proxy['port']}</code>\n"
            f"<b>Логін:</b> <code>{proxy['login']}</code>\n"
            f"<b>Пароль:</b> <code>{proxy['password']}</code>\n\n"
            f" 🛡️ <b>Тип:</b> {proxy['protocol']}\n"
            f" 🌎 <b>Країна:</b> {flag}{proxy['country_code']}\n"
            f" 📶 <b>Оператор:</b> {proxy['operator']}\n"
            f" 📅 <b>Орендовано:</b> {purchase_date}\n"
            f" ⏳ <b>Закінчується:</b> {expire_date}\n"
            f" ⏱️ <b>Залишилось:</b> {time_left_str}\n\n"
            f"🔗 <b>Підключення:</b>\n"
            f"<code>{connect_link}</code>\n\n"
            f"-------------------------------\n"
        )

    if len(proxies) > per_page:
        text += f"📖 Сторінка {page} з {total_pages} - використовуйте кнопки навігації"

    return text, total_pages

def get_pending_task_list_text(tasks: List[ProxyTaskQueue], page: int = 1, per_page: int = 3) -> Tuple[str, int]:
    if not tasks:
        return "⏳ Немає завдань", 0

    total_pages = (len(tasks) + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_tasks = tasks[start_idx:end_idx]

    text = f"📋 <b>Список завдань: {len(tasks)}</b>\n\n"

    for task in page_tasks:

        payload_info = ""
        if isinstance(task.payload, dict):

            for key, value in task.payload.items():
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, ensure_ascii=False, indent=2)
                    payload_info += f"  {key}: \n{value_str}\n"
                else:
                    payload_info += f"  {key}: {value}\n"
        else:
            payload_info += f"  {str(task.payload)}\n"

        text += (
            f"🆔 <b>ID:</b> {task.id}\n"
            f"📅 <b>Створено:</b> {task.created_at.strftime("%d.%m.%Y %H:%M:%S")}\n"
        )
        if task.updated_at:
            text += f"🔄 <b>Оновлено:</b> {task.updated_at.strftime("%d.%m.%Y %H:%M:%S")}\n"
            text += f"⏱️ <b>Час виконання:</b> {int((task.updated_at - task.created_at).total_seconds() * 1000)} мс\n"
        text +=(
            f"🔧 <b>Дія:</b> {task.task_type}\n"
            f"<pre>{payload_info}</pre>\n"
        )
        if task.error_message:
            text += f"<pre>{task.error_message}</pre>\n"

    if len(tasks) > per_page:
        text += f"\n📖 Сторінка {page} з {total_pages} - використовуйте кнопки навігації"

    return text, total_pages