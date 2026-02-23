"""
Репозиторий для работы с книгами в каталоге библиотеки.

Предоставляет расширенные методы поиска с фильтрацией по основным атрибутам книги,
поиск по уникальному ISBN и подсчёт результатов. Все операции выполняются асинхронно.
"""

from typing import Optional, Type, TypeVar

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import Select

from ..repositories.base_repository import BaseRepository
from ..models.book import Book

T = TypeVar("T")


class BookRepository(BaseRepository[Book]):
    """
    Репозиторий для управления сущностями книг.

    Расширяет базовый репозиторий специфичными методами поиска и фильтрации книг.
    """


    def __init__(self, session: AsyncSession):
        super().__init__(session, Book)

    async def find_by_filters(
            self,
            title: str | None = None,
            author: str | None = None,
            genre: str | None = None,
            year: int | None = None,
            available: bool | None = None,
            limit: int = 20,
            offset: int = 0,
    ) -> list[Book]:
        """
        Поиск книг с применением фильтров.

        Args:
            title: Подстрока для поиска в названии (case-insensitive)
            author: Подстрока для поиска в авторе (case-insensitive)
            genre: Точный матч жанра (case-insensitive)
            year: Точный год издания
            available: Фильтр по доступности (True/False)
            limit: Максимальное количество результатов (по умолчанию 20)
            offset: Смещение для пагинации (по умолчанию 0)

        Returns:
            Список книг, соответствующих фильтрам
        """
        query = select(Book)

        # Динамическое добавление фильтров (игнорируем None)
        if title:
            query = query.where(Book.title.ilike(f"%{title}%"))
        if author:
            query = query.where(Book.author.ilike(f"%{author}%"))
        if genre:
            query = query.where(Book.genre.ilike(f"%{genre}%"))
        if year is not None:
            query = query.where(Book.year == year)
        if available is not None:
            query = query.where(Book.available == available)

        # Применяем пагинацию
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def find_by_isbn(self, isbn: str) -> Book | None:
        """
        Найти книгу по уникальному ISBN.

        Args:
            isbn: ISBN книги (до 20 символов)

        Returns:
            Найденная книга или None, если не найдена
        """
        query = select(Book).where(Book.isbn == isbn)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_by_filters(
            self,
            title: str | None = None,
            author: str | None = None,
            genre: str | None = None,
            year: int | None = None,
            available: bool | None = None,
    ) -> int:
        """
        Подсчитать количество книг, соответствующих фильтрам.

        Args:
            title: Подстрока для поиска в названии (case-insensitive)
            author: Подстрока для поиска в авторе (case-insensitive)
            genre: Точный матч жанра (case-insensitive)
            year: Точный год издания
            available: Фильтр по доступности (True/False)

        Returns:
            Количество книг, удовлетворяющих условиям фильтрации
        """
        query = select(func.count(Book.book_id))

        # Те же фильтры, что и в find_by_filters
        if title:
            query = query.where(Book.title.ilike(f"%{title}%"))
        if author:
            query = query.where(Book.author.ilike(f"%{author}%"))
        if genre:
            query = query.where(Book.genre.ilike(f"%{genre}%"))
        if year is not None:
            query = query.where(Book.year == year)
        if available is not None:
            query = query.where(Book.available == available)

        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def find_available_books(
            self,
            limit: int = 20,
            offset: int = 0,
    ) -> list[Book]:
        """
        Получить список доступных для выдачи книг.

        Args:
            limit: Максимальное количество результатов
            offset: Смещение для пагинации

        Returns:
            Список доступных книг
        """
        query = (
            select(Book)
            .where(Book.available == True)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())