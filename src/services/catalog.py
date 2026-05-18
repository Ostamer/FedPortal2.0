# coding: utf-8
"""Реестр связей: тип сущности → endpoint, сервис, форматировщик."""
from __future__ import annotations

from functools import lru_cache
from typing import Dict, Optional

from src.models.definition import EntityDefinition
from src.models.enum import EntityType


def _entry(
    entity: EntityType,
    endpoint: str,
    service_cls: type,
    formatter_cls: type,
) -> tuple[str, EntityDefinition]:
    return entity.value, EntityDefinition(
        db_value=entity.value,
        endpoint=endpoint,
        service_cls=service_cls,
        formatter_cls=formatter_cls,
    )


def _build_registry() -> Dict[str, EntityDefinition]:
    from src.services.formatters import (
        ActivityFormatter,
        CertificateFormatter,
        DepartmentFormatter,
        EventFormatter,
        OrderFormatter,
        OrganizationFormatter,
        ParentsFormatter,
        ProgramGroupFinancingSourceFormatter,
        ProgramGroupFormatter,
    )
    from src.services.sync_services import (
        ActivitySyncService,
        ClassicSyncService,
        EventSyncService,
    )

    entries = [
        _entry(EntityType.ORGANIZATION, 'organization', ClassicSyncService, OrganizationFormatter),
        _entry(EntityType.DEPARTMENT, 'department', ClassicSyncService, DepartmentFormatter),
        _entry(EntityType.ORDER, 'order', ClassicSyncService, OrderFormatter),
        _entry(EntityType.EVENT, 'event', EventSyncService, EventFormatter),
        _entry(EntityType.ACTIVITY, 'activity', ActivitySyncService, ActivityFormatter),
        _entry(EntityType.PROGRAM_GROUP, 'program-group', ClassicSyncService, ProgramGroupFormatter),
        _entry(EntityType.CERTIFICATE, 'certificate', ClassicSyncService, CertificateFormatter),
        _entry(
            EntityType.PROGRAM_GROUP_FINANCING_SOURCE,
            'program-group-financing-source',
            ClassicSyncService,
            ProgramGroupFinancingSourceFormatter,
        ),
        _entry(EntityType.PARENTS, 'parents', ClassicSyncService, ParentsFormatter),
    ]
    return dict(entries)


@lru_cache(maxsize=1)
def get_registry() -> Dict[str, EntityDefinition]:
    return _build_registry()


def resolve_entity_type(name: str) -> Optional[str]:
    """Разрешить имя сущности в canonical db_value или None."""
    if name in get_registry():
        return name
    return None
