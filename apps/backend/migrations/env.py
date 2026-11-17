"""Entorno de Alembic. La URL sale de la configuración de la app (DATABASE_URL)."""

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  (registra las tablas en Base.metadata)
from app.config import get_settings
from app.db.base import Base

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    # Permite que los tests inyecten otra URL con `config.set_main_option`.
    return config.get_main_option("sqlalchemy.url") or get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = {**config.get_section(config.config_ini_section, {}), "sqlalchemy.url": _url()}
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        # batch: SQLite no soporta ALTER de restricciones; así sirve en ambos motores.
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
