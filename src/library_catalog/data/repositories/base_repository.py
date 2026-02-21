from typing import Generic, TypeVar, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def create(self, **kwargs) -> T:
        """Создать запись."""
        pass

    async def get_by_id(self, id: UUID) -> T | None:
        """
        Получить по ID.

        📝 Примечание: session.get() автоматически работает с primary key модели,
        независимо от его названия (id, book_id, user_id и т.д.)
        """
        pass

    async def update(self, id: UUID, **kwargs) -> T | None:
        """Обновить запись."""
        pass

    async def delete(self, id: UUID) -> bool:
        """Удалить запись."""
        pass

    async def get_all(
            self,
            limit: int = 100,
            offset: int = 0,
    ) -> list[T]:
        """Получить все записи с пагинацией."""
        pass