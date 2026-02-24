# library_catalog/src/library_catalog/api/v1/routers/books.py

from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request

from src.library_catalog.core.rate_limiter import limiter

# ДОБАВИТЬ ИМПОРТ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ:
from ...dependencies import BookServiceUowDep, UowDep, CurrentUserDep  # ← CurrentUserDep добавлен
from ..schemas.book import (
    BookCreate,
    BookUpdate,
    ShowBook,
    BookFilters,
)
from ..schemas.common import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/books", tags=["Books"])


# ========== CREATE (ЗАЩИЩЁН) ==========

@router.post(
    "/",
    response_model=ShowBook,
    status_code=status.HTTP_201_CREATED,
    summary="Создать книгу",
    description="Создать новую книгу в каталоге с автоматическим обогащением из Open Library",
)
@limiter.limit("3/minute")
async def create_book(
        request: Request,
        book_data: BookCreate,
        service: BookServiceUowDep,
        uow: UowDep,
        current_user: CurrentUserDep,  # ← ЗАЩИТА: только аутентифицированные пользователи
):
    """
    Создать новую книгу.

    🔒 Требуется аутентификация.
    """
    book = await service.create_book(book_data)
    await uow.commit()
    return book


# ========== READ (ПУБЛИЧНЫЕ — без защиты) ==========

@router.get(
    "/",
    response_model=PaginatedResponse[ShowBook],
    summary="Получить список книг",
    description="Получить список книг с фильтрацией и пагинацией",
)
async def get_books(
        service: BookServiceUowDep,
        pagination: Annotated[PaginationParams, Depends()],
        title: str | None = Query(None, description="Поиск по названию"),
        author: str | None = Query(None, description="Поиск по автору"),
        genre: str | None = Query(None, description="Фильтр по жанру"),
        year: int | None = Query(None, description="Фильтр по году"),
        available: bool | None = Query(None, description="Фильтр по доступности"),
):
    """
    Получить список книг с фильтрацией.

    🌐 Публичный эндпоинт — доступен всем без аутентификации.
    """
    books, total = await service.search_books(
        title=title,
        author=author,
        genre=genre,
        year=year,
        available=available,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return PaginatedResponse.create(books, total, pagination)


@router.get(
    "/{book_id}",
    response_model=ShowBook,
    summary="Получить книгу",
    description="Получить информацию о конкретной книге по ID",
)
async def get_book(
        book_id: UUID,
        service: BookServiceUowDep,
):
    """
    Получить книгу по ID.

    🌐 Публичный эндпоинт — доступен всем без аутентификации.

    Raises:
        404: Книга не найдена
    """
    book = await service.get_book(book_id)

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )

    return book


# ========== UPDATE (ЗАЩИЩЁН) ==========

@router.patch(
    "/{book_id}",
    response_model=ShowBook,
    summary="Обновить книгу",
    description="Частичное обновление книги (передаются только изменяемые поля)",
)
async def update_book(
        book_id: UUID,
        book_data: BookUpdate,
        service: BookServiceUowDep,
        uow: UowDep,
        current_user: CurrentUserDep,  # ← ЗАЩИТА
):
    """
    Обновить книгу.

    🔒 Требуется аутентификация.

    Передаются только те поля, которые нужно изменить.
    """
    book = await service.update_book(book_id, book_data)

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )

    await uow.commit()
    return book


# ========== DELETE (ЗАЩИЩЁН) ==========

@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить книгу",
    description="Удалить книгу из каталога",
)
async def delete_book(
        book_id: UUID,
        uow: UowDep,
        current_user: CurrentUserDep,  # ← ЗАЩИТА
):
    """
    Удалить книгу.

    🔒 Требуется аутентификация.

    Raises:
        404: Книга не найдена
    """
    success = await uow.books.delete(book_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )

    await uow.commit()
    return None