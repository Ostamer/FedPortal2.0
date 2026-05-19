"""
Публикация сообщений в Dead Letter Queues.
"""

import json
from datetime import datetime, timezone
from typing import Optional

import aio_pika

from src.config.logging import get_logger

logger = get_logger(__name__)


class DLQPublisher:
    """Публикует сообщения в DLQ (fatal или retry)."""

    def __init__(self, channel: aio_pika.RobustChannel):
        self._channel = channel

    async def publish(
        self,
        queue_name: str,
        original_body: bytes,
        reason: str,
        error: Optional[str] = None,
        http_status_code: Optional[int] = None,
    ) -> None:
        """
        Сформировать сообщение и опубликовать в указанную DLQ.

        Args:
            queue_name: имя dlq очереди (fatal или retry).
            original_body: сырые байты оригинального сообщения.
            reason: причина попадания в DLQ.
            error: текст ошибки.
            http_status_code: HTTP-статус от внешнего сервиса.
        """
        envelope = self._build_envelope(
            queue_name=queue_name,
            original_body=original_body,
            reason=reason,
            error=error,
            http_status_code=http_status_code,
        )

        await self._channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(envelope, ensure_ascii=False, default=str).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue_name,
        )

        logger.info(
            "message_published_to_dlq",
            queue=queue_name,
            reason=reason,
            http_status_code=http_status_code,
        )

    @staticmethod
    def _build_envelope(
        queue_name: str,
        original_body: bytes,
        reason: str,
        error: Optional[str],
        http_status_code: Optional[int],
    ) -> dict:
        """Собрать словарь-обёртку для сообщения в DLQ."""
        dlq_info: dict = {
            "queue": queue_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        }
        if error:
            dlq_info["error"] = error
        if http_status_code is not None:
            dlq_info["http_status_code"] = http_status_code

        try:
            original_message = json.loads(original_body.decode())
        except Exception:
            original_message = {"raw": original_body.decode(errors="replace")}

        return {
            "original_message": original_message,
            "dlq_info": dlq_info,
        }
