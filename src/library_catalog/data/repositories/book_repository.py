# src/library_catalog/data/repositories/book_repository.py
"""
Репозиторий для работы с книгами.
Реализует специфичные для книг операции поверх базового CRUD.
"""

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from .base_repository import BaseRepository
from ..models.book import Book


class BookRepository(BaseRepository[Book]):
    """Репозиторий для работы с книгами."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Book)

    # ========== ЗАЩИТА ОТ LIKE INJECTION ==========

    def _escape_like_pattern(self, pattern: str) -> str:
        """
        Экранировать специальные символы LIKE (% и _).

        Защищает от инъекций через фильтры поиска.
        Пример уязвимости:
            ?title=%' OR '1'='1  → найдёт ВСЕ книги

        После экранирования:
            ?title=%' OR '1'='1 → ищет буквально "%' OR '1'='1"
        """
        return (
            pattern
            .replace("\\", "\\\\")  # Сначала экранируем обратный слеш
            .replace("%", r"\%")    # Экранируем %
            .replace("_", r"\_")    # Экранируем _
        )

    # ========== ВЫНЕСЕНИЕ ОБЩЕЙ ЛОГИКИ ФИЛЬТРОВ (DRY) ==========

    def _apply_filters(
        self,
        query: Select,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
    ) -> Select:
        """
        Применить фильтры к SQL запросу.

        Используется в обоих методах (find_by_filters и count_by_filters)
        для предотвращения дублирования логики.

        Важно: Все текстовые фильтры экранируются для защиты от инъекций.
        """
        if title:
            escaped_title = self._escape_like_pattern(title)
            query = query.where(Book.title.ilike(f"%{escaped_title}%"))

        if author:
            escaped_author = self._escape_like_pattern(author)
            query = query.where(Book.author.ilike(f"%{escaped_author}%"))

        if genre:
            escaped_genre = self._escape_like_pattern(genre)
            query = query.where(Book.genre.ilike(f"%{escaped_genre}%"))

        if year is not None:
            query = query.where(Book.year == year)

        if available is not None:
            query = query.where(Book.available == available)

        return query

    # ========== ПОИСК С ФИЛЬТРАМИ ==========

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
        Поиск книг с применением фильтров и пагинацией.

        Примеры:
            # Поиск книг Роберта Мартина
            books = await repo.find_by_filters(author="Martin")

            # Поиск доступных книг по программированию
            books = await repo.find_by_filters(
                genre="Programming",
                available=True
            )

        Args:
            title: Подстрока в названии (без учёта регистра)
            author: Подстрока в авторе (без учёта регистра)
            genre: Подстрока в жанре (без учёта регистра)
            year: Точный год издания
            available: Фильтр по доступности
            limit: Максимум записей на страницу
            offset: Смещение для пагинации

        Returns:
            list[Book]: Список найденных книг
        """
        query = select(Book)
        query = self._apply_filters(query, title, author, genre, year, available)
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ========== ПОДСЧЁТ С ФИЛЬТРАМИ ==========

    async def count_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
    ) -> int:
        """
        Подсчитать количество книг по фильтрам.

        Использует тот же метод _apply_filters для избежания дублирования.
        """
        query = select(func.count(Book.book_id))
        query = self._apply_filters(query, title, author, genre, year, available)

        result = await self.session.execute(query)
        return result.scalar_one()

    # ========== ПОИСК ПО ISBN ==========

    async def find_by_isbn(self, isbn: str) -> Optional[Book]:
        """
        Найти книгу по точному совпадению ISBN.

        ISBN хранится в нормализованном виде (без дефисов и пробелов).
        """
        query = select(Book).where(Book.isbn == isbn)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()