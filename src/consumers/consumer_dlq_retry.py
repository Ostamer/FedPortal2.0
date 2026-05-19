"""
Консьюмер для очереди DLQ retry.
Читает сообщения из retry-очереди, ждёт заданную задержку и повторно отправляет original_message в основную очередь.
При превышении лимита попыток переносит сообщение в fatal DLQ.
"""

import asyncio
import json
from typing import Optional

import aio_pika

from src.clients.fed_portal import ExternalApiClient
from src.config.logging import get_logger
from src.config.main import settings
from src.consumers.dlq import DLQPublisher

logger = get_logger(__name__)


class DLQRetryConsumer:
    """Асинхронный консьюмер retry-DLQ с повторной публикацией в основную очередь."""

    def __init__(self, api_client: ExternalApiClient):
        self._api_client = api_client
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.RobustChannel] = None
        self._retry_queue: Optional[aio_pika.Queue] = None
        self._main_queue: Optional[aio_pika.Queue] = None
        self._is_running = False
        self._dlq_publisher: Optional[DLQPublisher] = None

    async def start(self) -> None:
        """Подключиться к RabbitMQ и начать consume retry-DLQ."""
        logger.info("dlq_retry_consumer_starting", host=settings.rabbitmq_host)

        self._connection = await aio_pika.connect_robust(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            login=settings.rabbitmq_user,
            password=settings.rabbitmq_password,
            virtualhost=settings.rabbitmq_vhost,
        )
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=1)

        await self._declare_queues()

        self._dlq_publisher = DLQPublisher(self._channel)

        await self._retry_queue.consume(self.handle)
        self._is_running = True
        logger.info(
            "dlq_retry_consumer_started",
            retry_queue=settings.dlq_retry,
            target_queue=settings.queue_sync,
            retry_delay_seconds=settings.retry_delay_seconds,
            retry_max_attempts=settings.retry_max_attempts,
        )

    async def stop(self) -> None:
        """Остановить retry-консьюмер и закрыть соединение."""
        logger.info("dlq_retry_consumer_stopping")
        self._is_running = False
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("dlq_retry_consumer_stopped")

    async def _declare_queues(self) -> None:
        """Объявить основную очередь и retry-очередь."""
        self._main_queue = await self._channel.declare_queue(
            settings.queue_sync,
            durable=True,
        )
        self._retry_queue = await self._channel.declare_queue(
            settings.dlq_retry,
            durable=True,
        )
        logger.debug(
            "dlq_retry_queues_declared",
            main=settings.queue_sync,
            retry=settings.dlq_retry,
        )

    async def handle(self, message: aio_pika.IncomingMessage) -> None:
        """Прочитать сообщение из retry-DLQ и вернуть original_message в основную очередь."""
        async with message.process(ignore_processed=True):
            try:
                envelope = json.loads(message.body.decode())
                original_message = envelope["original_message"]
                dlq_info = envelope.get("dlq_info", {})
                attempt = int(dlq_info.get("attempt", 1))
            except Exception as exc:
                logger.error(
                    "dlq_retry_message_invalid",
                    error=str(exc),
                    queue=settings.dlq_retry,
                )
                await message.ack()
                return

            if attempt >= settings.retry_max_attempts:
                await self._dlq_publisher.publish(
                    settings.dlq_fatal,
                    json.dumps(original_message, ensure_ascii=False, default=str).encode(),
                    reason="max_attempts",
                    error=f"Retry attempts exceeded: {attempt}",
                    attempt=attempt,
                )
                await message.ack()
                logger.warning(
                    "dlq_retry_message_moved_to_fatal",
                    from_queue=settings.dlq_retry,
                    to_queue=settings.dlq_fatal,
                    attempt=attempt,
                    reason="max_attempts",
                )
                return

            await asyncio.sleep(settings.retry_delay_seconds)

            republished_body = json.dumps(
                original_message,
                ensure_ascii=False,
                default=str,
            ).encode()

            await self._channel.default_exchange.publish(
                aio_pika.Message(
                    body=republished_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    headers={"x-retry-attempt": attempt},
                ),
                routing_key=settings.queue_sync,
            )

            await message.ack()
            logger.info(
                "dlq_retry_message_republished",
                from_queue=settings.dlq_retry,
                to_queue=settings.queue_sync,
                attempt=attempt,
                next_attempt=attempt + 1,
                retry_delay_seconds=settings.retry_delay_seconds,
            )
