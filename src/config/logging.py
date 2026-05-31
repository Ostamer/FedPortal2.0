import logging
import structlog
from src.config.main import settings


def setup_logging() -> None:
    """Настройка структурированного логирования."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO)
    )

    json_renderer = structlog.processors.JSONRenderer()
    console_renderer = structlog.dev.ConsoleRenderer()

    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        json_renderer if settings.log_format == "json" else console_renderer,
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Получить логер с указанным именем."""
    return structlog.get_logger(name)
