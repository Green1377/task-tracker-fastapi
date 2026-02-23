"""
Маппер для преобразования между моделью книги и схемой API.
"""

from typing import List
from ...data.models.book import Book
from ...api.v1.schemas.book import ShowBook


class BookMapper:
    """
    Маппер для преобразования между моделью книги и схемой API.

    Использует `model_validate()` из Pydantic v2 для автоматического маппинга.
    """

    @staticmethod
    def to_show_book(book: Book) -> ShowBook:
        """
        Преобразовать Book ORM модель в ShowBook DTO.

        Использует `model_validate()` для автоматического маппинга полей.
        Требует `from_attributes=True` в `model_config` схемы.

        Args:
            book: ORM модель из базы данных

        Returns:
            ShowBook: Pydantic модель для ответа API

        Raises:
            ValueError: Если маппинг не удался
        """
        try:
            return ShowBook.model_validate(book)
        except Exception as e:
            raise ValueError(f"Failed to map Book to ShowBook: {e}") from e

    @staticmethod
    def to_show_books(books: List[Book]) -> List[ShowBook]:
        """
        Преобразовать список книг в список схем.

        Args:
            books: Список ORM моделей

        Returns:
            List[ShowBook]: Список схем для ответа API
        """
        return [BookMapper.to_show_book(book) for book in books]