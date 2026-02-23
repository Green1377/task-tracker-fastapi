# src/library_catalog/data/uow.py
"""
Unit of Work pattern для управления транзакциями.
Обеспечивает атомарность операций над несколькими агрегатами.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from .repositories.book_repository import BookRepository  # ← КРИТИЧЕСКИ ВАЖНЫЙ ИМПОРТ


class UnitOfWork:
    """
    Unit of Work для управления транзакциями.

    Централизует управление транзакциями и предоставляет доступ ко всем репозиториям.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.books: BookRepository = BookRepository(session)
        # Добавьте другие репозитории по мере необходимости:
        # self.authors = AuthorRepository(session)

        self._committed = False

    async def __aenter__(self) -> "UnitOfWork":
        """Вход в контекстный менеджер."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Выход из контекстного менеджера.

        Автоматически откатывает транзакцию, если:
        - Произошло исключение
        - Не был вызван commit()
        """
        if exc_type is not None:
            # Исключение произошло - откатываем
            await self.rollback()
            return False  # Пробрасываем исключение дальше

        if not self._committed:
            # Commit не был вызван - откатываем для безопасности
            await self.rollback()

    async def commit(self) -> None:
        """Зафиксировать все изменения в транзакции."""
        await self.session.commit()
        self._committed = True

    async def rollback(self) -> None:
        """Откатить все изменения в транзакции."""
        await self.session.rollback()
        self._committed = False