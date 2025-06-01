from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from app.database.db import async_session


async def create_proxy_task_queue_trigger():
    """
    Creates a PostgreSQL trigger and function to notify listeners after a row is inserted
    into the `proxy_task_queue` table.

    This function:
        - Checks if the `notify_proxy_task_insert` function exists; creates it if missing.
        - Checks if the `trg_proxy_task_insert` trigger exists; creates it if missing.
        - The trigger calls `pg_notify` to send a notification on the 'proxy_task_event' channel
          with a JSON payload describing the inserted task.

    Raises:
        IntegrityError: If a commit fails due to a constraint or integrity issue.
    """
    async with async_session() as session:
        result_func = await session.execute(
            text("SELECT 1 FROM pg_proc WHERE proname = 'notify_proxy_task_insert'")
        )
        if result_func.scalar() is None:
            await session.execute(text("""
                CREATE FUNCTION notify_proxy_task_insert() RETURNS trigger AS $$
                BEGIN
                    PERFORM pg_notify(
                        'proxy_task_event',
                        json_build_object(
                            'task_id', NEW.id,
                            'task_type', NEW.task_type,
                            'server_ip', NEW.server_ip,
                            'payload', NEW.payload
                        )::text
                    );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """))

        result_trigger = await session.execute(
            text("SELECT 1 FROM pg_trigger WHERE tgname = 'trg_proxy_task_insert'")
        )
        if result_trigger.scalar() is None:
            await session.execute(text("""
                CREATE TRIGGER trg_proxy_task_insert
                AFTER INSERT ON proxy_task_queue
                FOR EACH ROW
                EXECUTE FUNCTION notify_proxy_task_insert();
            """))

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise

async def create_proxy_task_queue_update_trigger():
    """
    Creates a PostgreSQL trigger and function to automatically update the `updated_at` field
    when the `status` column in `proxy_task_queue` is changed to 'done' or 'error'.

    This function:
        - Checks for the `update_proxy_task_updated_at` function and creates it if missing.
        - Adds the `trg_update_proxy_task_updated_at` trigger on `proxy_task_queue` if missing.
        - The trigger fires BEFORE UPDATE and sets `updated_at` to `now()` only when `status` is
          changed and the new value is either 'done' or 'error'.

    Raises:
        IntegrityError: If a commit fails due to a constraint or integrity issue.
    """
    async with async_session() as session:
        result_func = await session.execute(
            text("SELECT 1 FROM pg_proc WHERE proname = 'update_proxy_task_updated_at'")
        )
        if result_func.scalar() is None:
            await session.execute(text("""
                CREATE OR REPLACE FUNCTION update_proxy_task_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF NEW.status IS DISTINCT FROM OLD.status AND NEW.status IN ('done', 'error') THEN
                        NEW.updated_at = now();
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """))

        result_trigger = await session.execute(
            text("SELECT 1 FROM pg_trigger WHERE tgname = 'trg_update_proxy_task_updated_at'")
        )
        if result_trigger.scalar() is None:
            await session.execute(text("""
                CREATE TRIGGER trg_update_proxy_task_updated_at
                BEFORE UPDATE ON proxy_task_queue
                FOR EACH ROW
                EXECUTE FUNCTION update_proxy_task_updated_at();
            """))

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise
