

from pydantic import BaseModel, Field


class OpenLibrarySearchDoc(BaseModel):
    """Документ из поиска Open Library."""

    title: str
    author_name: list[str] | None = Field(None)
    cover_i: int | None = Field(None)
    subject: list[str] | None = None
    description: str | None = None # ✅
    first_sentence: str | None = None # ✅
    publisher: list[str] | None = None
    language: list[str] | None = None
    ratings_average: float | None = Field(None)

    class Config:
        populate_by_name = True


class OpenLibrarySearchResponse(BaseModel):
    """Ответ от /search.json"""

    num_found: int = Field(..., alias="numFound")  # ✅ alias нужен только здесь
    docs: list[OpenLibrarySearchDoc]
    # Проблема: Если в ответе появятся новые поля (например, publish_year),
    # Pydantic по умолчанию проигнорирует их без предупреждения, но это может быть нежелательно для отладки.
    model_config = ConfigDict(populate_by_name=True, extra="ignore") # ✅