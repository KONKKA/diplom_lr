import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.database.requests.default_insert import insert_default_protocols, insert_default_statuses
from app.database.requests.tasks import clean_expired_proxy_rentals
from app.database.requests.triggers import create_proxy_task_queue_trigger, create_proxy_task_queue_update_trigger
from config import TOKEN

from app.database.db import async_main

from app.handlers.menu import router as menu_router
from app.handlers.registration import router as registration_router
from app.handlers.profile_settings import router as profile_settings_router
from app.handlers.catalog import router as catalog_router
from app.handlers.admin.panel import router as admin_router
from app.handlers.admin.add_proxies.add_operator_flow import router as add_operator_router
from app.handlers.admin.add_proxies.add_proxies_flow import router as add_proxy_router
from app.handlers.admin.edit_prices_flow import router as edit_prices_router
from app.handlers.admin.proxy_settings.proxy_settings import router as proxy_settings_router
from app.handlers.admin.add_proxies.add_servers_flow import router as add_server_router
from app.handlers.admin.add_proxies.add_ports_flow import router as add_ports_router
from app.handlers.my_proxies import router as my_proxies_router
from app.handlers.admin.task_queue import router as task_queue_router

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def main():
    await async_main()
    await insert_default_protocols()
    await insert_default_statuses()
    await create_proxy_task_queue_trigger()
    asyncio.create_task(clean_expired_proxy_rentals())
    await create_proxy_task_queue_update_trigger()
    print("Бот запущено...")

    dp.include_routers(
        menu_router,
        registration_router,
        admin_router,
        profile_settings_router,
        catalog_router,
        add_proxy_router,
        add_operator_router,
        edit_prices_router,
        proxy_settings_router,
        add_server_router,
        add_ports_router,
        my_proxies_router,
        task_queue_router
    )

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot Stopped")