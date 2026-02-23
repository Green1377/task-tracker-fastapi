from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...dependencies import BookServiceUowDep, UowDep  # ← Единый импорт
from ..schemas.book import (
    BookCreate,
    BookUpdate,
    ShowBook,
    BookFilters,
)
from ..schemas.common import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/books", tags=["Books"])


# ========== CREATE ==========

@router.post(
    "/",
    response_model=ShowBook,
    status_code=status.HTTP_201_CREATED,
    summary="Создать книгу",
    description="Создать новую книгу в каталоге с автоматическим обогащением из Open Library",
)
async def create_book(
        book_data: BookCreate,
        service: BookServiceUowDep,
        uow: UowDep,
):
    """
    Создать новую книгу.

    Использует явное управление транзакцией через Unit of Work.
    """
    book = await service.create_book(book_data)
    await uow.commit()  # ← Явный коммит
    return book


# ========== READ (не требуют коммита) ==========

@router.get(
    "/",
    response_model=PaginatedResponse[ShowBook],
    summary="Получить список книг",
    description="Получить список книг с фильтрацией и пагинацией",
)
async def get_books(
        service: BookServiceUowDep,  # ← Используем тот же деп для согласованности
        pagination: Annotated[PaginationParams, Depends()],
        title: str | None = Query(None, description="Поиск по названию"),
        author: str | None = Query(None, description="Поиск по автору"),
        genre: str | None = Query(None, description="Фильтр по жанру"),
        year: int | None = Query(None, description="Фильтр по году"),
        available: bool | None = Query(None, description="Фильтр по доступности"),
):
    """
    Получить список книг с фильтрацией.

    Read-only операция — коммит не требуется.
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
        service: BookServiceUowDep,  # ← Единый деп
):
    """
    Получить книгу по ID.

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


# ========== UPDATE ==========

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
        uow: UowDep,  # ← Добавить UoW для явного коммита
):
    """
    Обновить книгу.

    Передаются только те поля, которые нужно изменить.
    """
    book = await service.update_book(book_id, book_data)

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )

    await uow.commit()  # ← Явный коммит
    return book


# ========== DELETE ==========

@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить книгу",
    description="Удалить книгу из каталога",
)
async def delete_book(
        book_id: UUID,
        uow: UowDep,  # ← Используем напрямую для явного коммита
):
    """
    Удалить книгу.

    Raises:
        404: Книга не найдена
    """
    success = await uow.books.delete(book_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )

    await uow.commit()  # ← Явный коммит
    return None