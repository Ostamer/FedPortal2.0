# coding: utf-8
"""
Сервисы синхронизации.
"""
from typing import Any, Dict, Optional

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

    def _prepare_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Отформатировать и валидировать данные перед отправкой."""
        if not self.formatter.validate(data):
            return None

        try:
            return self.formatter.format(data)
        except (TypeError, ValueError) as exc:
            logger.warning(
                'sync_payload_format_failed',
                entity=self.entity_type,
                error=str(exc),
            )
            return None

    def _to_response(self, result: Dict[str, Any]) -> SyncResponse:
        return SyncResponse(
            http_status_code=result.get('http_status_code', 500),
            success=result.get('success', False),
            message=result.get('message'),
            data=result.get('data'),
            errors=result.get('errors'),
            err_code=result.get('err_code'),
        )

    async def create(self, data: Dict[str, Any]) -> SyncResponse:
        prepared = self._prepare_data(data)
        if prepared is None:
            return SyncResponse(http_status_code=400, success=False, message='Validation failed')

        result = await self.client.send(endpoint=self.endpoint, method='POST', json_data=prepared)
        logger.info('create_sync', entity=self.entity_type, status=result.get('http_status_code'))
        return self._to_response(result)

    async def update(self, concrete_id: int, data: Dict[str, Any]) -> SyncResponse:
        prepared = self._prepare_data(data)
        if prepared is None:
            return SyncResponse(http_status_code=400, success=False, message='Validation failed')

        result = await self.client.send(
            endpoint=self.endpoint,
            method='PUT',
            concrete_id=concrete_id,
            json_data=prepared,
        )
        logger.info('update_sync', entity=self.entity_type, id=concrete_id, status=result.get('http_status_code'))
        return self._to_response(result)

    async def delete(self, concrete_id: int) -> SyncResponse:
        result = await self.client.send(endpoint=self.endpoint, method='DELETE', concrete_id=concrete_id)
        logger.info('delete_sync', entity=self.entity_type, id=concrete_id, status=result.get('http_status_code'))
        return self._to_response(result)

    async def get(self, concrete_id: int) -> SyncResponse:
        result = await self.client.send(endpoint=self.endpoint, method='GET', concrete_id=concrete_id)
        logger.info('get_sync', entity=self.entity_type, id=concrete_id, status=result.get('http_status_code'))
        return self._to_response(result)


class PrefixedIdSyncService(ClassicSyncService):
    """Базовый сервис с префиксом ID для update/delete/get."""

    PREFIX: str = ''

    def _prefixed_id(self, concrete_id: int) -> str:
        return f'{self.PREFIX}{concrete_id}'

    async def update(self, concrete_id: int, data: Dict[str, Any]) -> SyncResponse:
        prepared = self._prepare_data(data)
        if prepared is None:
            return SyncResponse(http_status_code=400, success=False, message='Validation failed')

        prefixed_id = self._prefixed_id(concrete_id)
        result = await self.client.send(
            endpoint=self.endpoint,
            method='PUT',
            concrete_id=prefixed_id,
            json_data=prepared,
        )
        logger.info('update_sync', entity=self.entity_type, id=prefixed_id, status=result.get('http_status_code'))
        return self._to_response(result)

    async def delete(self, concrete_id: int) -> SyncResponse:
        prefixed_id = self._prefixed_id(concrete_id)
        result = await self.client.send(endpoint=self.endpoint, method='DELETE', concrete_id=prefixed_id)
        logger.info('delete_sync', entity=self.entity_type, id=prefixed_id, status=result.get('http_status_code'))
        return self._to_response(result)

    async def get(self, concrete_id: int) -> SyncResponse:
        prefixed_id = self._prefixed_id(concrete_id)
        result = await self.client.send(endpoint=self.endpoint, method='GET', concrete_id=prefixed_id)
        logger.info('get_sync', entity=self.entity_type, id=prefixed_id, status=result.get('http_status_code'))
        return self._to_response(result)


class EventSyncService(PrefixedIdSyncService):
    """Сервис для программ (event) — к ID добавляется префикс 2."""

    PREFIX = '2'


class ActivitySyncService(PrefixedIdSyncService):
    """Сервис для мероприятий (activity) — к ID добавляется префикс 1."""

    PREFIX = '1'
