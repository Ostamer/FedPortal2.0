"""
Конфигурация микросервиса.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    app_name: str = "Сервис интеграции с фед порталом"
    debug: bool = False

    # Адрес Фед портала
    fed_portal_api_url: str = ""
    # Ключ авторизации для Фед портала
    fed_portal_api_key: str = ""
    # Опциональный заголовок Host (для проксирования)
    fed_portal_api_host: Optional[str] = None
    # Проверять SSL-сертификат внешнего API
    fed_portal_verify_ssl: bool = True

    # Настройки RabbitMQ
    rabbitmq_host: str = ""
    rabbitmq_port: int = 0
    rabbitmq_user: str = ""
    rabbitmq_password: str = ""
    rabbitmq_vhost: str = ""

    # Наименование очередей RabbitMQ
    # Основная очередь для входящих записей синхронизации
    queue_sync: str = ""
    # Dead Letter Queue для сообщений,
    # которые не удалось обработать и необходимо обработать вручную (4xx ошибки)
    dlq_fatal: str = ""
    # Dead Letter Queue для сообщений,
    # которые не удалось обработать и сообщение нужно отправить повторно (5xx ошибки)
    dlq_retry: str = ""

    # Настройки базы данных PostgreSQL
    database_url: str = "postgresql+asyncpg://user:password@localhost/sync_db"

    # Retry / DLQ
    retry_delay_seconds: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


settings = Settings()
