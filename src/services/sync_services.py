"""
Сервисы синхронизации.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from src.clients.fed_portal import ExternalApiClient
from src.config.logging import get_logger
from src.schemas.base import SyncResponse
from src.services.formatters import BaseFormatter

logger = get_logger(__name__)


class BaseSyncService:
    """Базовый сервис синхронизации."""

    endpoint: str = ""

    async def create(self, data: Dict[str, Any]) -> SyncResponse:
        raise NotImplementedError

    async def update(self, concrete_id: int, data: Dict[str, Any]) -> SyncResponse:
        raise NotImplementedError

    async def delete(self, concrete_id: int) -> SyncResponse:
        raise NotImplementedError

    async def get(self, concrete_id: int) -> SyncResponse:
        raise NotImplementedError


class ClassicSyncService(BaseSyncService):
    """Универсальный сервис синхронизации для CRUD-операций."""

    def __init__(
        self,
        entity_type: str,
        endpoint: str,
        client: ExternalApiClient,
        formatter: BaseFormatter,
    ):
        self.entity_type = entity_type
        self.endpoint = endpoint
        self.client = client
        self.formatter = formatter

    def _resolve_id(self, concrete_id: int) -> Union[int, str]:
        """Преобразовать ID перед отправкой. Переопределяется в подклассах."""
        return concrete_id

    def _prepare_data(
        self, data: Dict[str, Any]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
        """Отформатировать и валидировать данные перед отправкой."""
        is_valid, errors = self.formatter.validate(data)
        if not is_valid:
            return None, errors

        try:
            return self.formatter.format(data), None
        except (TypeError, ValueError) as exc:
            logger.warning(
                'sync_payload_format_failed',
                entity=self.entity_type,
                error=str(exc),
            )
            return None, [
                {"field": "<root>", "reason": "format_failed", "error": str(exc)}
            ]

    def _to_response(self, result: Dict[str, Any]) -> SyncResponse:
        return SyncResponse(
            http_status_code=result.get('http_status_code', 500),
            success=result.get('success', False),
            message=result.get('message'),
            data=result.get('data'),
            errors=result.get('errors'),
            err_code=result.get('err_code'),
        )

    def _validation_error_response(
        self, errors: Optional[List[Dict[str, Any]]]
    ) -> SyncResponse:
        """Сформировать ответ с ошибками валидации."""
        formatted = []
        for err in (errors or []):
            field = err.get('loc', err.get('field', '<unknown>'))
            if isinstance(field, (list, tuple)):
                field = '.'.join(str(f) for f in field)
            formatted.append({
                'field': field,
                'message': err.get('msg', err.get('reason', 'Invalid value')),
                'value': err.get('input', err.get('value')),
            })

        return SyncResponse(
            http_status_code=400,
            success=False,
            message='Validation failed',
            errors={'validation_errors': formatted},
        )

    def _prepare_or_error(
        self, data: Dict[str, Any]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[SyncResponse]]:
        """Подготовить данные или вернуть готовый ответ с ошибкой."""
        prepared, errors = self._prepare_data(data)
        if prepared is None:
            return None, self._validation_error_response(errors)
        return prepared, None

    async def create(self, data: Dict[str, Any]) -> SyncResponse:
        prepared, error_response = self._prepare_or_error(data)
        if error_response:
            return error_response

        result = await self.client.send(
            endpoint=self.endpoint, method='POST', json_data=prepared
        )
        logger.info(
            'create_sync',
            entity=self.entity_type,
            status=result.get('http_status_code'),
        )
        return self._to_response(result)

    async def update(self, concrete_id: int, data: Dict[str, Any]) -> SyncResponse:
        prepared, error_response = self._prepare_or_error(data)
        if error_response:
            return error_response

        resolved_id = self._resolve_id(concrete_id)
        result = await self.client.send(
            endpoint=self.endpoint,
            method='PUT',
            concrete_id=resolved_id,
            json_data=prepared,
        )
        logger.info(
            'update_sync',
            entity=self.entity_type,
            id=resolved_id,
            status=result.get('http_status_code'),
        )
        return self._to_response(result)

    async def delete(self, concrete_id: int) -> SyncResponse:
        resolved_id = self._resolve_id(concrete_id)
        result = await self.client.send(
            endpoint=self.endpoint, method='DELETE', concrete_id=resolved_id
        )
        logger.info(
            'delete_sync',
            entity=self.entity_type,
            id=resolved_id,
            status=result.get('http_status_code'),
        )
        return self._to_response(result)

    async def get(self, concrete_id: int) -> SyncResponse:
        resolved_id = self._resolve_id(concrete_id)
        result = await self.client.send(
            endpoint=self.endpoint, method='GET', concrete_id=resolved_id
        )
        logger.info(
            'get_sync',
            entity=self.entity_type,
            id=resolved_id,
            status=result.get('http_status_code'),
        )
        return self._to_response(result)


class PrefixedIdSyncService(ClassicSyncService):
    """Сервис с префиксом ID для update/delete/get."""

    PREFIX: str = ''

    def _resolve_id(self, concrete_id: int) -> str:
        return f'{self.PREFIX}{concrete_id}'


class EventSyncService(PrefixedIdSyncService):
    """Сервис для программ (event) — к ID добавляется префикс 2."""

    PREFIX = '2'


class ActivitySyncService(PrefixedIdSyncService):
    """Сервис для мероприятий (activity) — к ID добавляется префикс 1."""

    PREFIX = '1'
