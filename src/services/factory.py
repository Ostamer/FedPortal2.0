# coding: utf-8
"""Фабрики сервисов и форматировщиков по типу сущности."""
from src.clients.fed_portal import ExternalApiClient
from src.config.logging import get_logger
from src.services.catalog import get_registry, resolve_entity_type
from src.services.formatters import BaseFormatter
from src.services.sync_services import BaseSyncService

logger = get_logger(__name__)


def get_sync_service(entity_type: str, client: ExternalApiClient) -> BaseSyncService:
    resolved = resolve_entity_type(entity_type)
    if resolved is None:
        raise ValueError(f'Неизвестный тип сущности: {entity_type}')

    config = get_registry()[resolved]
    return config.service_cls(resolved, config.endpoint, client, config.formatter_cls())


def get_formatter(entity_type: str) -> BaseFormatter:
    resolved = resolve_entity_type(entity_type)
    if resolved is None:
        logger.error('no_formatter_found', entity_type=entity_type)
        raise ValueError(f'Неизвестный тип сущности для форматирования: {entity_type}')

    config = get_registry()[resolved]
    return config.formatter_cls()
