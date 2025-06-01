from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardButton

from app.database.models import TaskStatusEnum
from app.database.requests.task_handler import get_tasks_by_status, delete_tasks_by_status
from app.filters.isAdmin import IsAdmin
from app.keyboards.admin.panel import get_task_queue_choice_keyboard
from app.keyboards.admin.proxy_settings import build_pagination_keyboard
from app.keyboards.universal_keyboards import get_confirm_or_cancel_keyboard
from app.utils.text_generator import get_pending_task_list_text

router = Router()

class WatchingTasksState(StatesGroup):
    is_watching_pending = State()
    is_watching_error = State()
    is_watching_done = State()

async def render_task_list(callback: CallbackQuery, state: FSMContext, status: TaskStatusEnum, page: int = 1):
    tasks = await get_tasks_by_status(status)

    if status is TaskStatusEnum.pending:
        await state.set_state(WatchingTasksState.is_watching_pending)
        text, total_pages = get_pending_task_list_text(tasks, page=page, per_page=3)
    elif status is TaskStatusEnum.error:
        await state.set_state(WatchingTasksState.is_watching_error)
        text, total_pages = get_pending_task_list_text(tasks, page=page, per_page=1)
    else:
        await state.set_state(WatchingTasksState.is_watching_done)
        text, total_pages = get_pending_task_list_text(tasks, page=page, per_page=1)

    clear_button = InlineKeyboardButton(text = "🧹 Очистити", callback_data="clear_queue")
    keyboard = build_pagination_keyboard(page=page, total_pages=total_pages, back_callback_data="task_queue", additional_button=clear_button)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(IsAdmin(), F.data == "task_queue")
async def handle_task_queue_choice_option(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🔘 <b>Оберіть дію:</b> ",parse_mode="HTML", reply_markup=get_task_queue_choice_keyboard())

#pending
@router.callback_query(IsAdmin(), F.data == "current_tasks_queue")
async def handle_current_tasks_queue(callback: CallbackQuery, state: FSMContext):
    await render_task_list(callback, state, TaskStatusEnum.pending, page=1)

@router.callback_query(IsAdmin(), WatchingTasksState.is_watching_pending, lambda c: c.data.startswith(("prev_", "next_")))
async def handle_pagination_current_tasks_queue(callback: CallbackQuery, state: FSMContext):
    action, page = callback.data.split("_")
    await render_task_list(callback, state=state, status=TaskStatusEnum.pending, page=int(page))

#error
@router.callback_query(IsAdmin(), F.data == "error_tasks_queue")
async def handle_error_tasks_queue(callback: CallbackQuery, state: FSMContext):
    await render_task_list(callback, state, TaskStatusEnum.error, page=1)

@router.callback_query(IsAdmin(), WatchingTasksState.is_watching_error, lambda c: c.data.startswith(("prev_", "next_")))
async def handle_pagination_error_tasks_queue(callback: CallbackQuery, state: FSMContext):
    action, page = callback.data.split("_")
    await render_task_list(callback, state=state, status=TaskStatusEnum.error, page=int(page))

#done
@router.callback_query(IsAdmin(), F.data == "done_tasks_queue")
async def handle_done_tasks_queue(callback: CallbackQuery, state: FSMContext):
    await render_task_list(callback, state, TaskStatusEnum.done, page=1)

@router.callback_query(IsAdmin(), WatchingTasksState.is_watching_done, lambda c: c.data.startswith(("prev_", "next_")))
async def handle_pagination_done_tasks_queue(callback: CallbackQuery, state: FSMContext):
    action, page = callback.data.split("_")
    await render_task_list(callback, state=state, status=TaskStatusEnum.done, page=int(page))

@router.callback_query(IsAdmin(), F.data == "clear_queue")
async def handle_clear_queue(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    if current_state == WatchingTasksState.is_watching_pending:
        queue_type = "ПОТОЧНУ ЧЕРГУ"
        description = "Усі завдання зі статусом 'очікує' будуть видалені"
    elif current_state == WatchingTasksState.is_watching_error:
        queue_type = "ЧЕРГУ ПОМИЛОК"
        description = "Усі завдання зі статусом 'помилка' будуть видалені"
    elif current_state == WatchingTasksState.is_watching_done:
        queue_type = "ЧЕРГУ ВИКОНАНИХ"
        description = "Усі завдання зі статусом 'виконано' будуть видалені"
    else:
        await callback.answer("❗ Невідомий тип черги")
        return

    confirmation_text = f"""
⚠️ <b>ПІДТВЕРДЖЕННЯ ДІЇ</b> ⚠️

Ви дійсно бажаєте очистити {queue_type}?

{description}

📊 <i>Ця дія є незворотною!</i>
"""

    keyboard = get_confirm_or_cancel_keyboard("confirm_queue_clear", "task_queue")
    await callback.message.edit_text(confirmation_text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(IsAdmin(), F.data == "confirm_queue_clear")
async def handle_clear_queue(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == WatchingTasksState.is_watching_pending:
        total, deleted = await delete_tasks_by_status(TaskStatusEnum.pending)
        status = "pending"
    elif current_state == WatchingTasksState.is_watching_error:
        total, deleted = await delete_tasks_by_status(TaskStatusEnum.error)
        status = "error"
    elif current_state == WatchingTasksState.is_watching_done:
        total, deleted = await delete_tasks_by_status(TaskStatusEnum.done)
        status = "done"
    else:
        await callback.answer("❗ Невідомий тип черги")
        return
    await callback.message.edit_text(f"♻️ Видалено {deleted}/{total} записів зі статусом {status}")
    await state.clear()
    await callback.message.answer("🔘 <b>Оберіть дію:</b> ", parse_mode="HTML",
                                     reply_markup=get_task_queue_choice_keyboard())
    await callback.answer()
