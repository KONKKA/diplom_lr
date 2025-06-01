
from sqlalchemy import text
from app.database.db import async_session


async def create_catalog_related_indexes():
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_proxy_catalog_proxy_type_id ON proxy_catalog(proxy_type_id)",
        "CREATE INDEX IF NOT EXISTS idx_proxy_catalog_available_amount ON proxy_catalog(available_amount)",
        "CREATE INDEX IF NOT EXISTS idx_proxy_type_id ON proxy_types(id)",
        "CREATE INDEX IF NOT EXISTS idx_proxy_type_protocol_id ON proxy_types(protocol_id)",
        "CREATE INDEX IF NOT EXISTS idx_proxy_type_operator_id ON proxy_types(operator_id)",
        "CREATE INDEX IF NOT EXISTS idx_protocol_id ON protocols(id)",
        "CREATE INDEX IF NOT EXISTS idx_operator_id ON operators(id)",
    ]

    async with async_session() as session:
        for stmt in index_statements:
            await session.execute(text(stmt))
        await session.commit()
