# tests/integration/test_api.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_book_endpoint(client: AsyncClient):
    """E2E тест создания книги."""
    response = await client.post(
        "/api/v1/books/",
        json={
            "title": "Clean Code",
            "author": "Robert Martin",
            "year": 2008,
            "genre": "Programming",
            "pages": 464
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Clean Code"
    assert "book_id" in data


@pytest.mark.asyncio
async def test_search_books(client: AsyncClient):
    """Тест поиска с фильтрами."""
    # Создать тестовые книги
    await client.post("/api/v1/books/", json={...})

    # Поиск по автору
    response = await client.get(
        "/api/v1/books/",
        params={"author": "Martin"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0