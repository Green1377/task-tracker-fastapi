# src/library_catalog/api/dependencies.py
"""
Зависимости для внедрения в FastAPI endpoints.
"""

from functools import lru_cache
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_db
from ..data.repositories.book_repository import BookRepository
from ..data.uow import UnitOfWork
from ..core.security import *
from ..domain.services.book_service import BookService
from ..external.openlibrary.client import OpenLibraryClient


# ========== EXTERNAL CLIENTS (Singletons) ==========

@lru_cache(maxsize=1)
def get_openlibrary_client() -> OpenLibraryClient:
    """Singleton для OpenLibraryClient."""
    return OpenLibraryClient(
        base_url=str(settings.openlibrary_base_url),
        timeout=settings.openlibrary_timeout,
    )


# ========== UNIT OF WORK ==========

async def get_uow(
        db: Annotated[AsyncSession, Depends(get_db)]
) -> AsyncGenerator[UnitOfWork, None]:
    """Зависимость для Unit of Work."""
    async with UnitOfWork(db) as uow:
        yield uow


# ========== REPOSITORIES ==========

async def get_book_repository(
        db: Annotated[AsyncSession, Depends(get_db)]
) -> BookRepository:
    """Создаёт репозиторий для текущей сессии БД."""
    return BookRepository(db)


# ========== SERVICES ==========

# Вариант 1: Для операций ЧТЕНИЯ (без управления транзакциями)
async def get_book_service(
        book_repo: Annotated[BookRepository, Depends(get_book_repository)],
        ol_client: Annotated[OpenLibraryClient, Depends(get_openlibrary_client)],
) -> BookService:
    """
    BookService для операций чтения.

    Использует репозиторий напрямую (без Unit of Work).
    Подходит для GET-запросов, где коммит не требуется.
    """
    return BookService(
        book_repository=book_repo,
        openlibrary_client=ol_client,
    )


# Вариант 2: Для операций ЗАПИСИ (с управлением транзакциями)
async def get_book_service_uow(
        uow: Annotated[UnitOfWork, Depends(get_uow)],
        ol_client: Annotated[OpenLibraryClient, Depends(get_openlibrary_client)],
) -> BookService:
    """
    BookService для операций записи.

    Использует репозиторий через Unit of Work.
    Требует явного вызова `await uow.commit()` после операции.
    """
    return BookService(
        book_repository=uow.books,
        openlibrary_client=ol_client,
    )


# ========== TYPE ALIASES ==========

# Для операций чтения (GET)
BookServiceDep = Annotated[BookService, Depends(get_book_service)]

# Для операций записи (POST, PATCH, DELETE)
BookServiceUowDep = Annotated[BookService, Depends(get_book_service_uow)]
UowDep = Annotated[UnitOfWork, Depends(get_uow)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db)]