"""
FastAPI-зависимости для роутеров.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.fed_portal import ExternalApiClient
from src.models.base import async_session
from src.models.enum import EntityType
from src.repositories.sync_record import SyncRecordRepository
from src.services.orchestrator import SyncOrchestrator
from src.services.factory import get_sync_service
from src.services.sync_services import BaseSyncService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Генератор сессии для FastAPI Depends."""
    async with async_session() as session:
        yield session


# Типизированная зависимость для сессии БД
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_external_api_client(request: Request) -> ExternalApiClient:
    """Получить HTTP-клиент из состояния приложения."""
    return request.app.state.client


def get_service(
    entity_type: EntityType = Path(...),
    client: ExternalApiClient = Depends(get_external_api_client),
) -> BaseSyncService:
    """Сервис синхронизации по типу сущности из пути."""
    try:
        return get_sync_service(entity_type, client)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def get_orchestrator(db: DbSessionDep) -> SyncOrchestrator:
    """Оркестратор синхронизации с репозиторием."""
    repo = SyncRecordRepository(db)
    return SyncOrchestrator(repo)
