from typing import Generic, Type, TypeVar
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Базовый репозиторий для CRUD операций.

    """

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def create(self, **kwargs) -> T:
        """
        Создать новую запись в БД.


        Args:
            **kwargs: Поля модели для создания

        Returns:
            T: Созданный объект с заполненными полями (включая сгенерированный ID)
        """
        instance = self.model(**kwargs)
        self.session.add(instance)

        # Сбросить в БД для получения сгенерированных значений (ID, timestamps)
        await self.session.flush()

        # Обновить объект с данными из БД
        await self.session.refresh(instance)

        return instance

    async def get_by_id(self, id: UUID) -> T | None:
        """
        Получить запись по первичному ключу.

        📝 Примечание: session.get() автоматически находит primary key
        модели, независимо от его имени (id, book_id, user_id и т.д.)

        Args:
            id: Значение первичного ключа

        Returns:
            T | None: Найденный объект или None если не существует
        """
        return await self.session.get(self.model, id)

    async def update(self, id: UUID, **kwargs) -> T | None:
        """
        Обновить существующую запись.


        Args:
            id: ID записи для обновления
            **kwargs: Поля для обновления (только переданные изменятся)

        Returns:
            T | None: Обновлённый объект или None если не найден
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return None

        # Обновляем только переданные атрибуты
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        # Сбросить изменения в БД
        await self.session.flush()

        # Обновить объект с данными из БД
        await self.session.refresh(instance)

        return instance

    async def delete(self, id: UUID) -> bool:
        """
        Удалить запись из БД.


        Args:
            id: ID записи для удаления

        Returns:
            bool: True если удалено успешно, False если не найдено
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return False

        await self.session.delete(instance)

        # Сбросить изменения в БД
        await self.session.flush()

        return True

    async def get_all(
            self,
            limit: int = 100,
            offset: int = 0,
    ) -> list[T]:
        """
        Получить все записи с пагинацией.


        Args:
            limit: Максимальное количество записей
            offset: Количество записей для пропуска

        Returns:
            list[T]: Список объектов модели
        """
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def flush(self) -> None:
        """
        Сбросить все изменения в БД без коммита.

        Полезно для получения сгенерированных значений (ID, timestamps)
        перед фиксацией транзакции.
        """
        await self.session.flush()