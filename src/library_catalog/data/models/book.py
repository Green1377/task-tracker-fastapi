"""
Модель книги для каталога библиотеки.

Представляет собой сущность книги с обязательными метаданными,
опциональными дополнительными полями и автоматическим отслеживанием времени создания/изменения.
Использует нативный UUID PostgreSQL для первичного ключа и оптимизирована индексами
для частых операций поиска и фильтрации.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base


class Book(Base):
    __tablename__ = "books"

    # Primary Key
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Уникальный идентификатор книги (UUID)",
    )

    # Обязательные поля
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="Название книги (до 500 символов)",
    )

    author: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
        comment="Автор книги (до 300 символов)",
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Год издания",
    )

    genre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Жанр книги (до 100 символов)",
    )

    pages: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Количество страниц",
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Доступна ли книга для выдачи",
    )

    # Опциональные поля
    isbn: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        comment="Международный стандартный книжный номер (до 20 символов)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Полное описание книги",
    )

    extra: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Дополнительные данные в формате JSON (издательство, серия, т.д.)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Время создания записи",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Время последнего обновления записи",
    )

    def __repr__(self) -> str:
        return f"<Book(id={self.book_id}, title='{self.title[:30]}{'...' if len(self.title) > 30 else ''}')>"

    def __str__(self) -> str:
        return f"{self.title} ({self.author}, {self.year})"


# Автоматическое обновление updated_at через event listener (надёжный способ)
@event.listens_for(Book, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)