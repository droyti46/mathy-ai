from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
    AsyncConnection,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import text


def _get_column_names(table_info_rows) -> set[str]:
    return {row[1] for row in table_info_rows}


async def _refresh_users_table_without_name(conn: AsyncConnection) -> None:
    await conn.execute(text("ALTER TABLE users RENAME TO users_old"))

    def _create_new_users_table(sync_conn):
        Base.metadata.tables["users"].create(sync_conn, checkfirst=False)

    await conn.run_sync(_create_new_users_table)
    await conn.execute(
        text(
            "INSERT INTO users (id, login, password_hash, created_at) "
            "SELECT "
            "    id, "
            "    CASE "
            "        WHEN login IS NOT NULL AND trim(login) != '' THEN login "
            "        WHEN name IS NOT NULL AND trim(name) != '' THEN name "
            "        ELSE id "
            "    END AS login, "
            "    password_hash, "
            "    created_at "
            "FROM users_old"
        )
    )
    await conn.execute(text("DROP TABLE users_old"))


async def _ensure_login_column(conn: AsyncConnection) -> None:
    table_info = await conn.execute(text("PRAGMA table_info(users)"))
    columns = list(table_info)
    column_names = _get_column_names(columns)

    if "login" not in column_names:
        if "email" in column_names:
            await conn.execute(text("ALTER TABLE users RENAME COLUMN email TO login"))
        else:
            await conn.execute(text("ALTER TABLE users ADD COLUMN login TEXT"))

        table_info = await conn.execute(text("PRAGMA table_info(users)"))
        columns = list(table_info)
        column_names = _get_column_names(columns)

    if "name" in column_names:
        await _refresh_users_table_without_name(conn)

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
        await _ensure_login_column(conn)
