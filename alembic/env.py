"""
Конфигурация Alembic для миграций (работает в синхронном режиме).
⚠️ Даже при асинхронном приложении, миграции выполняются синхронно!
"""

import sys
from pathlib import Path

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from alembic import context

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Импортируем настройки и базовый класс
from src.library_catalog.core.config import settings
from src.library_catalog.core.database import Base

# ИМПОРТИРУЕМ МОДЕЛИ (обязательно для обнаружения таблиц)
try:
    from src.library_catalog.data.models.book import Book  # noqa: F401
except ImportError:
    # Альтернативный путь (если структура другая)
    try:
        from src.library_catalog.models.book import Book  # noqa: F401
    except ImportError:
        raise ImportError(
            "Не найдена модель Book! Проверьте структуру проекта:\n"
            "Ожидаемые пути:\n"
            "  - src/library_catalog/data/models/book.py\n"
            "  - src/library_catalog/models/book.py"
        )

# this is the Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_sync_database_url() -> str:
    """
    Преобразует URL в синхронный формат для Alembic.

    Примеры преобразования:
        postgresql+asyncpg://user:pass@localhost/db
        → postgresql+psycopg2://user:pass@localhost/db

        postgresql://user:pass@localhost/db
        → postgresql+psycopg2://user:pass@localhost/db
    """
    url = str(settings.database_url)

    # Убираем asyncpg и заменяем на psycopg2
    url = url.replace("+asyncpg", "").replace("postgresql://", "postgresql+psycopg2://")

    return url


# Устанавливаем СИНХРОННЫЙ URL для Alembic
config.set_main_option("sqlalchemy.url", get_sync_database_url())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (без подключения к БД)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Выполнить миграции в контексте соединения."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (с подключением к БД).

    ⚠️ ИСПОЛЬЗУЕМ СИНХРОННЫЙ ДВИЖОК (не async_engine_from_config!)
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Отключаем пул для миграций
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()