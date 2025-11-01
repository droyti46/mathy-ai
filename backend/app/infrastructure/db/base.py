import json

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
    AsyncConnection,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import text


async def _ensure_user_columns(conn: AsyncConnection) -> None:
    columns_result = await conn.execute(text("PRAGMA table_info(users)"))
    column_names = {row[1] for row in columns_result}

    if "login" not in column_names:
        if "email" in column_names:
            await conn.execute(text("ALTER TABLE users RENAME COLUMN email TO login"))
        else:
            await conn.execute(text("ALTER TABLE users ADD COLUMN login TEXT"))

    if "name" not in column_names:
        await conn.execute(text("ALTER TABLE users ADD COLUMN name TEXT DEFAULT '' NOT NULL"))

    if "stats" not in column_names:
        default_stats_json = json.dumps(
            {
                "coins": 0,
                "solved_tasks": 0,
                "solved_task_ids": [],
                "streak_days": 0,
                "attempts": 0,
            }
        )
        default_stats_sql_literal = default_stats_json.replace("'", "''")
        alter_stats_column_sql = (
            "ALTER TABLE users ADD COLUMN stats TEXT DEFAULT '"
            + default_stats_sql_literal
            + "'"
        )
        await conn.execute(text(alter_stats_column_sql))
        await conn.execute(
            text(
                "UPDATE users SET stats = :default_stats WHERE stats IS NULL"
            ),
            {"default_stats": default_stats_json},
        )

    indexes_result = await conn.execute(text("PRAGMA index_list(users)"))
    index_names = {row[1] for row in indexes_result}

    if "ix_users_email" in index_names:
        await conn.execute(text("DROP INDEX IF EXISTS ix_users_email"))

    if "ix_users_login" not in index_names:
        await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_login ON users (login)"))

Base = declarative_base()

def create_engine_and_session(database_url: str):
    engine: AsyncEngine = create_async_engine(database_url, echo=False, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory

async def init_models(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_user_columns(conn)
