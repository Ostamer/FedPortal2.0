# coding: utf-8
"""
RabbitMQ консьюмер.
Отвечает только за управление соединением и жизненным циклом.
"""
from typing import Optional

import aio_pika
from src.config.logging import get_logger

from src.clients.fed_portal import ExternalApiClient
from src.config.main import settings
from src.consumers.dlq import DLQPublisher
from src.consumers.handler import MessageHandler

logger = get_logger(__name__)


class MessageConsumer:
    """Асинхронный консьюмер RabbitMQ."""

    def __init__(self, api_client: ExternalApiClient):
        self._api_client = api_client
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.RobustChannel] = None
        self._queue: Optional[aio_pika.Queue] = None
        self._is_running = False
        self._handler: Optional[MessageHandler] = None

    async def start(self) -> None:
        """Подключиться к RabbitMQ и начать consume."""
        logger.info("consumer_starting", host=settings.rabbitmq_host)

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

        dlq = DLQPublisher(self._channel)
        self._handler = MessageHandler(dlq, self._api_client)

        await self._queue.consume(self._handler.handle)
        self._is_running = True
        logger.info("consumer_started", queue=settings.queue_sync)

    async def stop(self) -> None:
        """Остановить консьюмер и закрыть соединение."""
        logger.info("consumer_stopping")
        self._is_running = False
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("consumer_stopped")

    async def _declare_queues(self) -> None:
        """Объявить основную очередь, DLQ retry, DLQ fatal ."""
        self._queue = await self._channel.declare_queue(
            settings.queue_sync,
            durable=True,
        )
        await self._channel.declare_queue(settings.dlq_fatal, durable=True)
        await self._channel.declare_queue(settings.dlq_retry, durable=True)
        logger.debug(
            "queues_declared",
            main=settings.queue_sync,
            fatal=settings.dlq_fatal,
            retry=settings.dlq_retry,
        )



