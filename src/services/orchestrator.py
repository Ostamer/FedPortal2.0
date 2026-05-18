# coding: utf-8
"""
Оркестратор синхронизации: общая логика для REST и RabbitMQ.
Централизует: логирование, вызов сервиса, обновление реестра, commit.
"""
from typing import Any, Awaitable, Callable, Dict, Optional

from src.config.logging import get_logger
from src.models.enum import EntityType
from src.repositories.sync_record import SyncRecordRepository
from src.schemas.base import SyncResponse

logger = get_logger(__name__)


class SyncOrchestrator:
    """Оркестратор синхронизации: логирование, вызов сервиса, обновление реестра."""

    def __init__(self, repo: SyncRecordRepository):
        self._repo = repo

    @staticmethod
    def build_response_payload(result: SyncResponse) -> dict:
        """Преобразовать SyncResponse в dict для записи в лог."""
        payload: dict = {
            'http_status_code': result.http_status_code,
            'success': result.success,
        }
        if result.data is not None:
            payload['data'] = result.data
        if result.message is not None:
            payload['message'] = result.message
        if result.errors is not None:
            payload['errors'] = result.errors
        if result.err_code is not None:
            payload['err_code'] = result.err_code
        return payload

    async def execute(
        self,
        entity_type: EntityType,
        action: str,
        object_id: Optional[int],
        payload: Optional[Dict[str, Any]],
        service_coro: Callable[[], Awaitable[SyncResponse]],
    ) -> SyncResponse:
        """
        Выполнить синхронизацию с полным логированием и обновлением реестра.

        Args:
            entity_type: тип сущности.
            action: действие (create, get, update, delete).
            object_id: ID объекта.
            payload: данные для отправки (может быть None для get/delete).
            service_coro: асинхронная функция вызова сервиса.

        Returns:
            SyncResponse от сервиса.

        Raises:
            Exception: пробрасывает исключение сервиса (вызывающая сторона обрабатывает).
        """
        request_data: dict = {
            'entity_type': entity_type.value,
            'action': action,
        }
        if object_id is not None:
            request_data['object_id'] = object_id
        if payload is not None:
            request_data['payload'] = payload

        log = await self._repo.create_log(request_data)

        try:
            result = await service_coro()
        except Exception:
            await self._repo.rollback()
            raise

        await self._repo.update_log(log, self.build_response_payload(result))

        if result.success:
            await self._update_registry(entity_type, action, object_id, payload)

        await self._repo.commit()
        return result

    async def _update_registry(
        self,
        entity_type: EntityType,
        action: str,
        object_id: Optional[int],
        payload: Optional[Dict[str, Any]],
    ) -> None:
        """Обновить реестр синхронизированных сущностей при успехе."""
        if action == 'delete' and object_id is not None:
            await self._repo.delete(entity_type, object_id)
        elif object_id is not None:
            await self._repo.upsert(entity_type, object_id)
        elif payload is not None and isinstance(payload, dict) and payload.get('id') is not None:
            await self._repo.upsert(entity_type, payload['id'])

    async def log_error(
        self,
        entity_type: EntityType,
        action: str,
        object_id: Optional[int],
        payload: Optional[Dict[str, Any]],
        error_payload: dict,
    ) -> None:
        """
        Записать ошибку в лог и закоммитить (для REST endpoints).

        Args:
            entity_type: тип сущности.
            action: действие.
            object_id: ID объекта.
            payload: данные запроса.
            error_payload: данные ошибки для лога.
        """
        request_data: dict = {
            'entity_type': entity_type.value,
            'action': action,
        }
        if object_id is not None:
            request_data['object_id'] = object_id
        if payload is not None:
            request_data['payload'] = payload

        log = await self._repo.create_log(request_data)
        await self._repo.update_log(log, error_payload)
        await self._repo.commit()
