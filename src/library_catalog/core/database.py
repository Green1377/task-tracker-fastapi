"""
База данных и зависимости для работы с БД.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


# Создать асинхронный движок
engine = create_async_engine(
    str(settings.database_url),
    pool_size=settings.database_pool_size,
    max_overflow=10,  # ← Дополнительные соединения при перегрузке
    echo=settings.debug,
    pool_pre_ping=True,  # ← Проверять соединения перед использованием
)

# Создать фабрику сессий
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # ← Сохраняем объекты после коммита
    autocommit=False,  # ← Явно отключаем автокоммит
    autoflush=False,  # ← КРИТИЧНО! Контролируемый flush через репозиторий
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии БД.

    Используется в роутерах через Depends(get_db).

    Обрабатывает исключения с автоматическим откатом транзакции.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            # Откатить транзакцию при ошибке
            await session.rollback()
            raise
        # Сессия автоматически закроется при выходе из контекста


async def dispose_engine() -> None:
    """
    Закрыть все соединения с БД.

    Вызывается при завершении работы приложения (в lifespan).
    """
    await engine.dispose()