# src/library_catalog/core/security.py
"""
JWT аутентификация и авторизация.

Этот модуль предоставляет:
- Генерацию и валидацию JWT токенов
- Защиту эндпоинтов через зависимости
- Хеширование паролей (для будущего использования)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings

# ========== КОНСТАНТЫ ==========

# Алгоритм хеширования паролей (bcrypt - современный и безопасный)
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer схема для получения токена из заголовка Authorization
SECURITY = HTTPBearer()


# ========== СХЕМЫ ДЛЯ API ==========

class TokenData(BaseModel):
    """
    Данные, извлекаемые из токена.

    Содержит только необходимую информацию для идентификации пользователя.
    """
    username: Optional[str] = None
    user_id: Optional[str] = None  # Можно добавить UUID пользователя


class Token(BaseModel):
    """
    Схема ответа с токеном.

    Используется для возврата токена клиенту после успешной аутентификации.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Время жизни токена в секундах


# ========== ХЕШИРОВАНИЕ ПАРОЛЕЙ ==========

def get_password_hash(password: str) -> str:
    """
    Хешировать пароль для безопасного хранения в БД.

    Args:
        password: Исходный пароль в открытом виде

    Returns:
        str: Хешированный пароль (начинается с $2b$...)

    Пример:
        >>> hash = get_password_hash("secret123")
        >>> hash
        '$2b$12$...'
    """
    return PWD_CONTEXT.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверить пароль против хеша.

    Сравнивает введённый пароль с хешем из БД.

    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хеш из базы данных

    Returns:
        bool: True если пароли совпадают, иначе False

    Пример:
        >>> hash = get_password_hash("secret123")
        >>> verify_password("secret123", hash)
        True
        >>> verify_password("wrong", hash)
        False
    """
    return PWD_CONTEXT.verify(plain_password, hashed_password)


# ========== JWT ТОКЕНЫ ==========

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создать JWT access токен.

    Токен содержит:
    - sub (subject): идентификатор пользователя
    - exp (expiration): время истечения
    - iat (issued at): время создания

    ⚠️ ВАЖНО: Данные в токене НЕ шифруются, только подписываются!
    Не храните чувствительную информацию (пароли, персональные данные).

    Пример:
        >>> token = create_access_token(
        ...     data={"sub": "user@example.com", "user_id": "123"},
        ...     expires_delta=timedelta(hours=1)
        ... )

    Args:
        data: Полезная нагрузка (обычно username или user_id)
        expires_delta: Время жизни токена. Если None - используется настройка из конфига

    Returns:
        str: Подписанный JWT токен
    """
    to_encode = data.copy()

    # Определить время истечения
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    # Добавить стандартные клеймы JWT
    to_encode.update({
        "exp": expire,  # Время истечения
        "iat": datetime.now(timezone.utc)  # Время создания
    })

    # Подписать токен секретным ключом
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


# ========== ЗАВИСИМОСТЬ ДЛЯ ЗАЩИТЫ ЭНДПОИНТОВ ==========

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(SECURITY)
) -> TokenData:
    """
    Получить текущего пользователя из JWT токена.

    Используется как зависимость в защищённых эндпоинтах.

    🔒 Как это работает:
    1. FastAPI извлекает заголовок Authorization из запроса
    2. Проверяет формат: "Bearer <token>"
    3. Передаёт токен в эту функцию
    4. Функция декодирует и валидирует токен
    5. Возвращает данные пользователя или выбрасывает 401 ошибку

    Пример использования в роутере:
        @router.post("/books/")
        async def create_book(
            book_data: BookCreate,
            current_user: TokenData = Depends(get_current_user)  # ← Защита!
        ):
            # Только аутентифицированные пользователи попадут сюда
            ...

    Args:
        credentials: Объект с токеном из заголовка Authorization

    Returns:
        TokenData: Данные пользователя из токена

    Raises:
        HTTPException(401): Если токен отсутствует, невалиден или просрочен
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Декодировать токен
        payload = jwt.decode(
            credentials.credentials,  # Сам токен
            settings.jwt_secret_key,  # Секретный ключ для проверки подписи
            algorithms=[settings.jwt_algorithm]  # Алгоритм
        )

        # Извлечь имя пользователя из токена
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # Создать объект с данными пользователя
        token_data = TokenData(username=username)

        return token_data

    except JWTError:
        # Любая ошибка декодирования → 401
        raise credentials_exception


# ========== TYPE ALIAS ДЛЯ УДОБСТВА ==========

"""
Пример использования:
    from ..core.security import CurrentUser

    @router.get("/me")
    async def get_profile(current_user: CurrentUser):
        return {"username": current_user.username}
"""
CurrentUser = TokenData