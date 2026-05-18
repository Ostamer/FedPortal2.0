# coding: utf-8
"""
Оркестратор обработки одного сообщения из RabbitMQ.
Парсинг → вызов сервиса → запись результата → ack / DLQ.
"""
import json
from typing import Optional

import aio_pika
import httpx
from pydantic import ValidationError

from src.clients.fed_portal import ExternalApiClient
from src.config.logging import get_logger
from src.config.main import settings
from src.consumers.dlq import DLQPublisher
from src.models.base import async_session
from src.models.enum import EntityType
from src.repositories.sync_record import SyncRecordRepository
from src.schemas.base import RabbitMessage, SyncResponse
from src.services.orchestrator import SyncOrchestrator
from src.services.factory import get_sync_service

logger = get_logger(__name__)


class MessageHandler:
    """Обрабатывает одно входящее сообщение из очереди."""

    def __init__(self, dlq: DLQPublisher, api_client: ExternalApiClient):
        self._dlq = dlq
        self._api_client = api_client

    async def handle(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(ignore_processed=True):
            # Получаем тело сообщения
            body = message.body

            parsed = await self._parse(body)
            if parsed is None:
                await message.ack()
                return

            data, msg = parsed

            logger.info(
                'message_received',
                entity=msg.entity_type,
                action=msg.action,
                object_id=msg.object_id,
            )

            if msg.action not in {'create', 'update', 'delete', 'get'}:
                logger.warning('unknown_action', action=msg.action)
                await self._dlq.publish(
                    settings.dlq_fatal,
                    body,
                    reason='unknown_action',
                    error=f'Unknown action: {msg.action}',
                )
                await message.ack()
                return

            async with async_session() as session:
                repo = SyncRecordRepository(session)
                orchestrator = SyncOrchestrator(repo)

                try:
                    service = get_sync_service(msg.entity_type, self._api_client)
                    result = await orchestrator.execute(
                        entity_type=EntityType(msg.entity_type),
                        action=msg.action,
                        object_id=msg.object_id,
                        payload=msg.payload,
                        service_coro=lambda: self._dispatch(service, msg),
                    )
                except (ValueError, TypeError, ValidationError) as exc:
                    logger.warning('sync_fatal_exception', error=str(exc), entity=msg.entity_type, action=msg.action)
                    await self._dlq.publish(
                        settings.dlq_fatal,
                        body,
                        reason='fatal_exception',
                        error=str(exc),
                    )
                    await message.ack()
                    return
                except (httpx.TimeoutException, httpx.RequestError) as exc:
                    logger.error('sync_retry_exception', error=str(exc), entity=msg.entity_type, action=msg.action)
                    await self._dlq.publish(
                        settings.dlq_retry,
                        body,
                        reason='transient_exception',
                        error=str(exc),
                    )
                    await message.ack()
                    return
                except Exception as exc:
                    logger.error('sync_retry_exception', error=str(exc), entity=msg.entity_type, action=msg.action)
                    await self._dlq.publish(
                        settings.dlq_retry,
                        body,
                        reason='unexpected_exception',
                        error=str(exc),
                    )
                    await message.ack()
                    return

                await self._route_by_status(message, msg, result, body)

    async def _parse(self, body: bytes) -> Optional[tuple[dict, RabbitMessage]]:
        """Распарсить тело сообщения. При ошибке — отправить в fatal DLQ."""
        try:
            data = json.loads(body.decode())
        except Exception as exc:
            logger.error('invalid_json_format', error=str(exc))
            await self._dlq.publish(
                settings.dlq_fatal,
                body,
                reason='invalid_json_format',
                error=str(exc),
            )
            return None

        try:
            return data, RabbitMessage(**data)
        except Exception as exc:
            logger.error('invalid_message_schema', error=str(exc))
            await self._dlq.publish(
                settings.dlq_fatal,
                body,
                reason='invalid_message_schema',
                error=str(exc),
            )
            return None

    async def _dispatch(self, service, msg: RabbitMessage) -> SyncResponse:
        """Маршрутизация по action."""
        if msg.action == 'create':
            return await service.create(msg.payload)
        if msg.action == 'update':
            payload = msg.payload or {'id': msg.object_id}
            return await service.update(msg.object_id, payload)
        if msg.action == 'delete':
            return await service.delete(msg.object_id)
        # get
        return await service.get(msg.object_id)

    async def _route_by_status(
        self,
        message: aio_pika.IncomingMessage,
        msg: RabbitMessage,
        result: SyncResponse,
        body: bytes,
    ) -> None:
        """Решить — ack или DLQ — на основе HTTP-статуса результата."""
        status = result.http_status_code

        if result.success:
            await message.ack()
            logger.info('message_processed', object_id=msg.object_id, status=status)
        elif httpx.codes.is_client_error(status):
            await self._dlq.publish(
                settings.dlq_fatal,
                body,
                reason='client_error',
                error=result.message,
                http_status_code=status,
            )
            await message.ack()
            logger.warning('message_moved_to_dlq_fatal', object_id=msg.object_id, status=status)
        elif httpx.codes.is_server_error(status):
            await self._dlq.publish(
                settings.dlq_retry,
                body,
                reason='server_error',
                error=result.message,
                http_status_code=status,
            )
            await message.ack()
            logger.warning('message_moved_to_dlq_retry', object_id=msg.object_id, status=status)
        else:
            await self._dlq.publish(
                settings.dlq_retry,
                body,
                reason='unexpected_status',
                error=result.message,
                http_status_code=status,
            )
            await message.ack()
            logger.warning(
                'message_moved_to_dlq_retry',
                object_id=msg.object_id,
                status=status,
                reason='unexpected_status',
            )

