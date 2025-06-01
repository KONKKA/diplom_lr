import asyncio
from typing import List, Tuple

from sqlalchemy import select, func, delete

from app.database.db import async_session
from app.database.models import (
    ProxyServer, Proxy, ProxyPorts, Protocol,
    Operator, ProxyType, ProxyTaskQueue, TaskStatusEnum
)
from app.database.requests.get_data import get_task_status


async def add_task_to_queue(
    proxy_id: int,
    port_id: int,
    login: str,
    password: str,
    task_type: str = "add_proxy"
) -> int:
    """
    Add a new proxy-related task to the task queue.

    Args:
        proxy_id (int): ID of the proxy to be used in the task.
        port_id (int): ID of the port assigned to the proxy.
        login (str): Login credential for the proxy.
        password (str): Password credential for the proxy.
        task_type (str, optional): Type of task to be performed. Defaults to "add_proxy".

    Returns:
        int: The ID of the newly created task.

    Raises:
        ValueError: If required data for the task could not be found.
    """
    async with async_session() as session:
        result = await session.execute(
            select(
                ProxyServer.ip.label("server_ip"),
                Proxy.internal_ip,
                ProxyPorts.port,
                Protocol.value.label("protocol"),
                Operator.name.label("operator")
            ).join(Proxy, ProxyServer.id == Proxy.server_id)
             .join(ProxyType, ProxyType.id == Proxy.proxy_type_id)
             .join(Protocol, Protocol.id == ProxyType.protocol_id)
             .join(Operator, Operator.id == ProxyType.operator_id)
             .join(ProxyPorts, ProxyPorts.id == port_id)
             .where(Proxy.id == proxy_id)
        )
        data = result.first()
        if data is None:
            raise ValueError("Could not find data for the task")

        task = ProxyTaskQueue(
            task_type=task_type,
            server_ip=data.server_ip,
            payload={
                "ip": data.server_ip,
                "internal_ip": data.internal_ip,
                "port": data.port,
                "login": login,
                "password": password,
                "protocol": data.protocol,
                "operator": data.operator
            }
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task.id


async def wait_for_task_completion(task_id: int, timeout: int = 60, interval: int = 2) -> bool:
    """
    Wait until a task is completed or failed, or the timeout is reached.

    Args:
        task_id (int): ID of the task to monitor.
        timeout (int, optional): Maximum time to wait in seconds. Defaults to 60.
        interval (int, optional): Interval between status checks in seconds. Defaults to 2.

    Returns:
        bool: True if the task completed successfully, False if failed or timeout.
    """
    waited = 0
    while waited < timeout:
        status = await get_task_status(task_id)
        if status == "done":
            return True
        elif status == "error":
            return False
        await asyncio.sleep(interval)
        waited += interval
    return False


async def get_tasks_by_status(status: TaskStatusEnum) -> List[ProxyTaskQueue]:
    """
    Retrieve all tasks from the queue that have a specific status.

    Args:
        status (TaskStatusEnum): The task status to filter by.

    Returns:
        List[ProxyTaskQueue]: List of tasks matching the given status.
    """
    async with async_session() as session:
        stmt = select(ProxyTaskQueue).where(
            ProxyTaskQueue.status == status
        ).order_by(ProxyTaskQueue.created_at)

        result = await session.execute(stmt)
        return result.scalars().all()


async def delete_tasks_by_status(status: TaskStatusEnum) -> Tuple[int, int]:
    """
    Delete all tasks from the queue that have a specific status.

    Args:
        status (TaskStatusEnum): The status of the tasks to delete.

    Returns:
        Tuple[int, int]: A tuple where the first element is the number of matching tasks,
                         and the second element is the number of rows actually deleted.

    Raises:
        Exception: If an error occurs during deletion, the exception is logged and re-raised.
    """
    async with async_session() as session:
        try:
            count_stmt = select(func.count()).where(ProxyTaskQueue.status == status)
            total_count = (await session.execute(count_stmt)).scalar()

            if total_count == 0:
                return (0, 0)

            delete_stmt = delete(ProxyTaskQueue).where(
                ProxyTaskQueue.status == status
            )
            result = await session.execute(delete_stmt)
            await session.commit()

            return (total_count, result.rowcount)

        except Exception as e:
            await session.rollback()
            print(f"Error while deleting tasks: {e}")
            raise
