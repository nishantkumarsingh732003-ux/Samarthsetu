"""Alembic environment.

The application talks to Postgres over asyncpg. Alembic runs its migrations through
the same async engine online, and renders plain SQL offline (`alembic upgrade head
--sql`) using the psycopg driver name so the DDL can be reviewed without a database.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import settings

# Importing the model package registers every table on Base.metadata.
from app.models import Base  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# PostGIS and pgvector install their own objects into the database. Autogenerate must
# not try to drop or recreate them.
IGNORED_TABLES = {"spatial_ref_sys", "geography_columns", "geometry_columns", "raster_columns",
                  "raster_overviews"}


def include_object(object_, name, type_, reflected, compare_to):  # noqa: ANN001, ANN201
    return not (type_ == "table" and name in IGNORED_TABLES)


def _sync_url() -> str:
    """Offline mode renders SQL only, so strip the async driver from the URL."""
    return settings.DATABASE_URL.replace("+asyncpg", "")


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = settings.DATABASE_URL
    connectable = async_engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
