"""Тесты DLQ (Dead Letter Queue) — обработка ошибочных сообщений.

Проверяем публикацию в retry и fatal очереди, формирование reason и логирование.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from aio_pika import DeliveryMode

from src.consumers.dlq import DLQManager


class TestDLQManagerPublishRetry:
    """Тесты публикации в retry-очередь (временные ошибки)."""

    @pytest.mark.asyncio
    async def test_publish_retry_with_original_body(self):
        channel = MagicMock()
        exchange = AsyncMock()
        channel.default_exchange = exchange
        dlq = DLQManager(channel, retry_queue_name="test.retry", fatal_queue_name="test.fatal")
        await dlq.publish("test.retry", b"original body", reason="server_error", http_status_code=503)
        exchange.publish.assert_awaited_once()
        call_args = exchange.publish.call_args
        message = call_args.args[0]
        assert message.body == b"original body"
        assert message.headers["x-reason"] == "server_error"
        assert message.headers["x-http-status-code"] == 503
        assert message.delivery_mode == DeliveryMode.PERSISTENT

    @pytest.mark.asyncio
    async def test_publish_retry_without_http_status(self):
        channel = MagicMock()
        exchange = AsyncMock()
        channel.default_exchange = exchange
        dlq = DLQManager(channel, retry_queue_name="test.retry", fatal_queue_name="test.fatal")
        await dlq.publish("test.retry", b"body", reason="timeout")
        message = exchange.publish.call_args.args[0]
        assert message.headers["x-reason"] == "timeout"
        assert "x-http-status-code" not in message.headers


class TestDLQManagerPublishFatal:
    """Тесты публикации в fatal-очередь (неисправимые ошибки)."""

    @pytest.mark.asyncio
    async def test_publish_fatal_with_error(self):
        channel = MagicMock()
        exchange = AsyncMock()
        channel.default_exchange = exchange
        dlq = DLQManager(channel, retry_queue_name="test.retry", fatal_queue_name="test.fatal")
        try:
            raise ValueError("bad payload")
        except ValueError as e:
            await dlq.publish("test.fatal", b"body", reason="fatal_exception", error=e)
        message = exchange.publish.call_args.args[0]
        assert message.headers["x-reason"] == "fatal_exception"
        assert "ValueError: bad payload" in message.headers["x-error"]

    @pytest.mark.asyncio
    async def test_publish_fatal_without_error(self):
        channel = MagicMock()
        exchange = AsyncMock()
        channel.default_exchange = exchange
        dlq = DLQManager(channel, retry_queue_name="test.retry", fatal_queue_name="test.fatal")
        await dlq.publish("test.fatal", b"body", reason="invalid_json_format")
        message = exchange.publish.call_args.args[0]
        assert message.headers["x-reason"] == "invalid_json_format"
        assert "x-error" not in message.headers
