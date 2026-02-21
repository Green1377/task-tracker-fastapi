
from uuid import UUID
from typing import Optional


class AppException(Exception):
    """Базовое исключение приложения."""

    def __init__(
            self,
            message: str,
            status_code: int = 500,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    """Исключение для не найденных ресурсов."""

    def __init__(
            self,
            resource: str,
            identifier: Optional[str] = None,
    ):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message=message, status_code=404)


class BookNotFoundException(NotFoundException):
    """Книга не найдена."""
    def __init__(self, book_id: UUID):
        super().__init__(resource="Book", identifier=book_id)

class BookAlreadyExistsException(AppException):
    """Книга с таким ISBN уже существует."""
    def __init__(self, isbn: str):
        super().__init__(
            message=f"Book with ISBN '{isbn}' already exists",
            status_code=409,
        )

class InvalidYearException(AppException):
    """Невалидный год издания."""
    def __init__(self, year: int):
        from datetime import datetime
        current_year = datetime.now().year
        super().__init__(
            message=f"Year {year} is invalid (must be 1000-{current_year})",
            status_code=400,
        )

class InvalidPagesException(AppException):
    """Невалидное количество страниц."""
    def __init__(self, pages: int):
        super().__init__(
            message=f"Pages count must be positive, got {pages}",
            status_code=400,
        )

class OpenLibraryException(AppException):
    """Ошибка Open Library API."""
    def __init__(self, message: str):
        super().__init__(
            message=f"Open Library API error: {message}",
            status_code=503,
        )

class OpenLibraryTimeoutException(AppException):
    """Таймаут при обращении к Open Library API."""
    def __init__(self, timeout: float):
        super().__init__(
            message=f"Open Library API timeout after {timeout}s",
            status_code=504,
        )