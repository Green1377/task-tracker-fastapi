from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    # ========== ОСНОВНЫЕ НАСТРОЙКИ ==========
    app_name: str = "Library Catalog API"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    database_url: PostgresDsn
    database_pool_size: int = 20
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    # ========== CORS (ИСПРАВЛЕНО ДЛЯ БЕЗОПАСНОСТИ) ==========
    cors_origins: list[str] = ["http://localhost:3000"]  # ✅ Безопасный дефолт

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v, info):
        """
        Запретить опасную комбинацию: '*' + credentials.

        В продакшене wildcard запрещён при использовании авторизации.
        """
        # Преобразовать строку в список (для .env: CORS_ORIGINS="a,b,c")
        if isinstance(v, str):
            v = [origin.strip() for origin in v.split(",") if origin.strip()]

        environment = info.data.get("environment", "development")

        if "*" in v and environment == "production":
            raise ValueError(
                "CORS wildcard (*) not allowed in production with credentials. "
                "Set specific origins via CORS_ORIGINS environment variable."
            )

        return v

    # ========== OPEN LIBRARY ==========
    openlibrary_base_url: str = "https://openlibrary.org"
    openlibrary_timeout: float = 10.0

    # ========== JWT АУТЕНТИФИКАЦИЯ (НОВОЕ) ==========
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-this-in-production-please-1234567890",
        description=(
            "Секретный ключ для подписи JWT токенов. "
            "⚠️ ОБЯЗАТЕЛЬНО измените в .env в продакшене! "
            "Генерация: `openssl rand -hex 32`"
        )
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Алгоритм шифрования JWT"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="Время жизни access токена в минутах"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="Время жизни refresh токена в днях"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()