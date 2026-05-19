from fastapi import APIRouter, Body, Depends, HTTPException

from src.config.logging import get_logger
from src.dependency_injection import get_orchestrator, get_service
from src.models.enum import EntityType, SyncSource
from src.schemas.base import SyncResponse
from src.services.orchestrator import SyncOrchestrator
from src.services.sync_services import BaseSyncService

logger = get_logger(__name__)

sync_router = APIRouter(tags=['sync'])


@sync_router.post(
    '/{entity_type}',
    response_model=SyncResponse,
    status_code=201,
    summary='Создать сущность во внешнем API',
)
async def create(
    entity_type: EntityType,
    orchestrator: SyncOrchestrator = Depends(get_orchestrator),
    data: dict = Body(...),
    service: BaseSyncService = Depends(get_service),
) -> SyncResponse:
    try:
        result = await orchestrator.execute(
            entity_type=entity_type,
            action='create',
            object_id=None,
            payload=data,
            service_coro=lambda: service.create(data),
            source=SyncSource.MANUAL,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('create_error', entity=entity_type, error=str(exc))
        await orchestrator.log_error(
            entity_type=entity_type,
            action='create',
            object_id=None,
            payload=data,
            error_payload={'http_status_code': 500, 'success': False, 'message': str(exc)},
            source=SyncSource.MANUAL,
        )
        raise HTTPException(status_code=500, detail=str(exc))

    if not result.success:
        raise HTTPException(status_code=result.http_status_code, detail=result.message or 'Create failed')

    return result


@sync_router.get(
    '/{entity_type}/{concrete_id}',
    response_model=SyncResponse,
    summary='Получить сущность из внешнего API',
)
async def get(
    concrete_id: int,
    entity_type: EntityType,
    orchestrator: SyncOrchestrator = Depends(get_orchestrator),
    service: BaseSyncService = Depends(get_service),
) -> SyncResponse:
    try:
        result = await orchestrator.execute(
            entity_type=entity_type,
            action='get',
            object_id=concrete_id,
            payload=None,
            service_coro=lambda: service.get(concrete_id),
            source=SyncSource.MANUAL,
        )
    except Exception as exc:
        logger.error('get_error', entity=entity_type, id=concrete_id, error=str(exc))
        await orchestrator.log_error(
            entity_type=entity_type,
            action='get',
            object_id=concrete_id,
            payload=None,
            error_payload={'http_status_code': 500, 'success': False, 'message': str(exc)},
            source=SyncSource.MANUAL,
        )
        raise HTTPException(status_code=500, detail=str(exc))

    if not result.success:
        raise HTTPException(status_code=result.http_status_code, detail=result.message or 'Get failed')

    return result


@sync_router.put(
    '/{entity_type}/{concrete_id}',
    response_model=SyncResponse,
    summary='Обновить сущность во внешнем API',
)
async def update(
    concrete_id: int,
    entity_type: EntityType,
    orchestrator: SyncOrchestrator = Depends(get_orchestrator),
    data: dict = Body(...),
    service: BaseSyncService = Depends(get_service),
) -> SyncResponse:
    try:
        result = await orchestrator.execute(
            entity_type=entity_type,
            action='update',
            object_id=concrete_id,
            payload=data,
            service_coro=lambda: service.update(concrete_id, data),
            source=SyncSource.MANUAL,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('update_error', entity=entity_type, id=concrete_id, error=str(exc))
        await orchestrator.log_error(
            entity_type=entity_type,
            action='update',
            object_id=concrete_id,
            payload=data,
            error_payload={'http_status_code': 500, 'success': False, 'message': str(exc)},
            source=SyncSource.MANUAL,
        )
        raise HTTPException(status_code=500, detail=str(exc))

    if not result.success:
        raise HTTPException(status_code=result.http_status_code, detail=result.message or 'Update failed')

    return result


@sync_router.delete(
    '/{entity_type}/{concrete_id}',
    status_code=204,
    summary='Удалить сущность из внешнего API',
)
async def delete(
    concrete_id: int,
    entity_type: EntityType,
    orchestrator: SyncOrchestrator = Depends(get_orchestrator),
    service: BaseSyncService = Depends(get_service),
) -> None:
    try:
        result = await orchestrator.execute(
            entity_type=entity_type,
            action='delete',
            object_id=concrete_id,
            payload=None,
            service_coro=lambda: service.delete(concrete_id),
            source=SyncSource.MANUAL,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error('delete_error', entity=entity_type, id=concrete_id, error=str(exc))
        await orchestrator.log_error(
            entity_type=entity_type,
            action='delete',
            object_id=concrete_id,
            payload=None,
            error_payload={'http_status_code': 500, 'success': False, 'message': str(exc)},
            source=SyncSource.MANUAL,
        )
        raise HTTPException(status_code=500, detail=str(exc))

    if not result.success:
        raise HTTPException(status_code=result.http_status_code, detail=result.message or 'Delete failed')
