# tests/unit/test_book_service.py
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_book_success():
    """Успешное создание книги."""
    # Arrange
    mock_repo = AsyncMock()
    mock_ol_client = AsyncMock()

    mock_repo.find_by_isbn.return_value = None
    mock_repo.create.return_value = create_mock_book()
    mock_ol_client.enrich.return_value = {}

    service = BookService(mock_repo, mock_ol_client)

    book_data = BookCreate(
        title="Test Book",
        author="Test Author",
        year=2020,
        genre="Fiction",
        pages=100
    )

    # Act
    result = await service.create_book(book_data)

    # Assert
    assert result.title == "Test Book"
    mock_repo.create.assert_called_once()
    mock_ol_client.enrich.assert_called_once()


@pytest.mark.asyncio
async def test_create_book_duplicate_isbn():
    """Ошибка при дублирующемся ISBN."""
    mock_repo = AsyncMock()
    mock_repo.find_by_isbn.return_value = create_mock_book()

    service = BookService(mock_repo, AsyncMock())

    book_data = BookCreate(
        title="Test",
        author="Test",
        year=2020,
        genre="Fiction",
        pages=100,
        isbn="123"
    )

    with pytest.raises(BookAlreadyExistsException):
        await service.create_book(book_data)