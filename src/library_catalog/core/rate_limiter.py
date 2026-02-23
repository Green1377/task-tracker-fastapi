"""
Глобальный рейт лимитер для защиты API.
Вынесен в отдельный модуль для избежания циклических импортов.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# ЕДИНСТВЕННЫЙ экземпляр лимитера для всего приложения
limiter = Limiter(key_func=get_remote_address)