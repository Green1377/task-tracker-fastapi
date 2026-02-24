# src/library_catalog/api/routes/auth.py
"""
Эндпоинты аутентификации.

Предоставляет:
- Получение JWT токена
- Обновление токена (опционально)
- Информация о текущем пользователе
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.library_catalog.core.rate_limiter import limiter

from ...dependencies import DbSessionDep
from src.library_catalog.core.config import settings
from src.library_catalog.core.security import (
    create_access_token,
    CurrentUser,
    get_current_user,
    Token,
    verify_password,
)

router = APIRouter(tags=["auth"])

# HTTP Basic Auth для простоты (в продакшене заменить на полноценную аутентификацию)
security = HTTPBasic()


@router.post(
    "/token",
    response_model=Token,
    summary="Получить JWT токен",
    description="""
    Аутентифицировать пользователя и получить access token.

    🔐 Метод аутентификации:
    - Использует HTTP Basic Auth (username:password в заголовке)
    - В продакшене заменить на эндпоинт с JSON телом

    📝 Пример использования:
    ```bash
    curl -X POST http://localhost:8000/api/v1/token \\
      -u "admin:secret"
    ```

    ⏱ Токен действителен: 30 минут (по умолчанию)
    """
)
@limiter.limit("5/minute")
async def login(
        request: Request,
        credentials: HTTPBasicCredentials = Depends(security),
        db: DbSessionDep = None,  # Можно добавить проверку в БД
):
    """
    Получить JWT токен для аутентификации.

    ⚠️ ВРЕМЕННАЯ РЕАЛИЗАЦИЯ:
    Сейчас используется простая проверка в памяти.
    В продакшене нужно:
    1. Добавить модель пользователя в БД
    2. Проверять учётные данные в БД
    3. Хешировать пароли через bcrypt

    Args:
        credentials: Учётные данные из заголовка Authorization
        db: Сессия БД (для будущей проверки в БД)

    Returns:
        Token: Объект с access_token и метаданными

    Raises:
        HTTPException(401): Если учётные данные неверны
    """
    # ❌ ВРЕМЕННО: простая проверка в памяти
    # В продакшене заменить на проверку в БД!

    correct_username = "admin"
    correct_password = "secret"

    # Проверить учётные данные
    # В реальном приложении здесь будет запрос к БД
    if credentials.username != correct_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
            headers={"WWW-Authenticate": "Basic"},
        )

    if credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Basic"},
        )

    # ✅ Учётные данные верны - создать токен

    # Определить время жизни токена
    access_token_expires = timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )

    # Создать JWT токен
    access_token = create_access_token(
        data={
            "sub": credentials.username,
            # Можно добавить дополнительные данные:
            # "user_id": str(user.id),
            # "role": user.role,
        },
        expires_delta=access_token_expires
    )

    # Вернуть токен клиенту
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds())
    )


@router.get(
    "/me",
    response_model=dict,
    summary="Получить информацию о текущем пользователе",
    description="""
    Возвращает информацию о пользователе, связанном с токеном.

    🔒 Требуется аутентификация: передайте токен в заголовке:
    ```
    Authorization: Bearer <your_token_here>
    ```
    """
)
async def read_users_me(
        current_user: CurrentUser = Depends(get_current_user)
):
    """
    Получить информацию о текущем аутентифицированном пользователе.

    Эндпоинт защищён через `get_current_user` зависимость.
    Только пользователи с валидным токеном могут получить доступ.

    Args:
        current_user: Данные пользователя из токена (автоматически извлекаются)

    Returns:
        dict: Информация о пользователе
    """
    return {
        "username": current_user.username,
        "authenticated": True
    }


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выйти из системы",
    description="""
    Завершить сессию пользователя.

    🔒 Требуется аутентификация.

    💡 Примечание: Поскольку JWT stateless, этот эндпоинт
    не делает ничего на сервере. Клиент должен удалить токен.
    В будущем можно добавить блэклист токенов.
    """
)
async def logout(
        current_user: CurrentUser = Depends(get_current_user)
):
    """
    Выйти из системы.

    В случае JWT токенов "выход" означает удаление токена на клиенте.
    Сервер не хранит состояние, поэтому здесь ничего не происходит.

    В будущем можно реализовать:
    - Redis блэклист для отозванных токенов
    - Хранение токенов в БД для отслеживания

    Args:
        current_user: Текущий пользователь (проверка аутентификации)
    """
    # В случае JWT ничего не делаем - клиент сам удалит токен
    return None