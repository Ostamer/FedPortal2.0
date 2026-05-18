# coding: utf-8
"""Описание конфигурации одной сущности в реестре интеграции."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from src.services.formatters import BaseFormatter
    from src.services.sync_services import BaseSyncService


@dataclass(frozen=True)
class EntityDefinition:
    db_value: str
    endpoint: str
    service_cls: Type[BaseSyncService]
    formatter_cls: Type[BaseFormatter]
