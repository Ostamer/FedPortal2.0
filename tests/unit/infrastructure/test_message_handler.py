"""Тесты обработчика сообщений RabbitMQ (MessageHandler).

Проверяем парсинг, маршрутизацию, DLQ, ack и обработку исключений.
"""
import json
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import aio_pika
import httpx
import pytest
from pydantic import ValidationError

from src.consumers.handler import MessageHandler
from src.schemas.base import RabbitMessage, SyncResponse


class DummyProcessContext:
    def __init__(self, message):
        self._message = message

    async def __aenter__(self):
        return self._message

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyIncomingMessage:
    def __init__(self, body: bytes):
        self.body = body
        self.acked = 0
        self._processed = False

    def process(self, ignore_processed=True):
        return DummyProcessContext(self)

    async def ack(self):
        self.acked += 1


class DummyDLQ:
    def __init__(self):
        self.published = []

    async def publish(self, queue_name, body, reason, error=None, http_status_code=None):
        self.published.append({
            "queue_name": queue_name,
            "body": body,
            "reason": reason,
            "error": error,
            "http_status_code": http_status_code,
        })


class DummySessionContext:
    async def __aenter__(self):
        return MagicMock()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyRepo:
    def __init__(self, session):
        self.session = session


class DummyOrchestratorSuccess:
    def __init__(self, repo):
        self.repo = repo

    async def execute(self, **kwargs):
        return SyncResponse(http_status_code=200, success=True)


class DummyOrchestratorTimeout:
    def __init__(self, repo):
        self.repo = repo

    async def execute(self, **kwargs):
        raise httpx.TimeoutException("timeout", request=httpx.Request("GET", "https://example.com"))


class DummyOrchestratorClientError:
    def __init__(self, repo):
        self.repo = repo

    async def execute(self, **kwargs):
        return SyncResponse(http_status_code=400, success=False, message="bad request")


class DummyOrchestratorServerError:
    def __init__(self, repo):
        self.repo = repo

    async def execute(self, **kwargs):
        return SyncResponse(http_status_code=503, success=False, message="upstream down")


@pytest.fixture
def handler():
    dlq = DummyDLQ()
    api_client = MagicMock()
    return MessageHandler(dlq=dlq, api_client=api_client)


@pytest.fixture
def valid_payload():
    return {
        "entity_type": "organization",
        "action": "create",
        "object_id": 1,
        "payload": {"id": 1, "name": "Test"},
    }


class TestMessageHandlerParse:
    """Тесты метода _parse."""

    @pytest.mark.asyncio
    async def test_parse_valid_message(self, handler, valid_payload):
        body = json.dumps(valid_payload).encode()
        result = await handler._parse(body)
        assert result is not None
        data, msg = result
        assert msg.entity_type == "organization"
        assert msg.action == "create"
        assert msg.object_id == 1

    @pytest.mark.asyncio
    async def test_parse_invalid_json_goes_to_fatal_dlq(self, handler):
        body = b"{invalid"
        result = await handler._parse(body)
        assert result is None
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "invalid_json_format"

    @pytest.mark.asyncio
    async def test_parse_invalid_schema_goes_to_fatal_dlq(self, handler):
        body = json.dumps({"entity_type": "organization"}).encode()
        result = await handler._parse(body)
        assert result is None
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "invalid_message_schema"


class TestMessageHandlerRouteByStatus:
    """Тесты метода _route_by_status."""

    @pytest.mark.asyncio
    async def test_success_acks_message(self, handler, valid_payload):
        message = DummyIncomingMessage(body=b"{}")
        msg = RabbitMessage(**valid_payload)
        result = SyncResponse(http_status_code=200, success=True)

        await handler._route_by_status(message, msg, result, body=b"{}")
        assert message.acked == 1
        assert len(handler._dlq.published) == 0

    @pytest.mark.asyncio
    async def test_4xx_goes_to_fatal_dlq(self, handler, valid_payload):
        message = DummyIncomingMessage(body=b"{}")
        msg = RabbitMessage(**valid_payload)
        result = SyncResponse(http_status_code=400, success=False, message="bad request")

        await handler._route_by_status(message, msg, result, body=b"{}")
        assert message.acked == 1
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "client_error"
        assert handler._dlq.published[0]["http_status_code"] == 400

    @pytest.mark.asyncio
    async def test_5xx_goes_to_retry_dlq(self, handler, valid_payload):
        message = DummyIncomingMessage(body=b"{}")
        msg = RabbitMessage(**valid_payload)
        result = SyncResponse(http_status_code=503, success=False, message="upstream down")

        await handler._route_by_status(message, msg, result, body=b"{}")
        assert message.acked == 1
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "server_error"
        assert handler._dlq.published[0]["http_status_code"] == 503

    @pytest.mark.asyncio
    async def test_unexpected_status_goes_to_retry_dlq(self, handler, valid_payload):
        message = DummyIncomingMessage(body=b"{}")
        msg = RabbitMessage(**valid_payload)
        result = SyncResponse(http_status_code=302, success=False, message="redirect")

        await handler._route_by_status(message, msg, result, body=b"{}")
        assert message.acked == 1
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "unexpected_status"


class TestMessageHandlerHandle:
    """Тесты полного цикла handle."""

    @pytest.mark.asyncio
    async def test_handle_success(self, monkeypatch, handler, valid_payload):
        import src.consumers.handler as handler_module

        monkeypatch.setattr(handler_module, "async_session", lambda: DummySessionContext())
        monkeypatch.setattr(handler_module, "SyncRecordRepository", DummyRepo)
        monkeypatch.setattr(handler_module, "SyncOrchestrator", DummyOrchestratorSuccess)
        monkeypatch.setattr(handler_module, "get_sync_service", lambda *args, **kwargs: MagicMock())

        message = DummyIncomingMessage(body=json.dumps(valid_payload).encode())
        await handler.handle(message)

        assert message.acked == 1
        assert len(handler._dlq.published) == 0

    @pytest.mark.asyncio
    async def test_handle_unknown_action_goes_to_fatal(self, monkeypatch, handler):
        import src.consumers.handler as handler_module

        monkeypatch.setattr(handler_module, "async_session", lambda: DummySessionContext())

        payload = {
            "entity_type": "organization",
            "action": "patch",
            "object_id": 1,
            "payload": {},
        }
        message = DummyIncomingMessage(body=json.dumps(payload).encode())
        await handler.handle(message)

        assert message.acked == 1
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "unknown_action"

    @pytest.mark.asyncio
    async def test_handle_value_error_goes_to_fatal(self, monkeypatch, handler, valid_payload):
        import src.consumers.handler as handler_module

        monkeypatch.setattr(handler_module, "async_session", lambda: DummySessionContext())
        monkeypatch.setattr(handler_module, "SyncRecordRepository", DummyRepo)
        monkeypatch.setattr(handler_module, "SyncOrchestrator", DummyOrchestratorSuccess)

        def raise_value_error(*args, **kwargs):
            raise ValueError("bad payload")

        monkeypatch.setattr(handler_module, "get_sync_service", raise_value_error)

        message = DummyIncomingMessage(body=json.dumps(valid_payload).encode())
        await handler.handle(message)

        assert message.acked == 1
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "fatal_exception"

    @pytest.mark.asyncio
    async def test_handle_timeout_goes_to_retry(self, monkeypatch, handler, valid_payload):
        import src.consumers.handler as handler_module

        monkeypatch.setattr(handler_module, "async_session", lambda: DummySessionContext())
        monkeypatch.setattr(handler_module, "SyncRecordRepository", DummyRepo)
        monkeypatch.setattr(handler_module, "SyncOrchestrator", DummyOrchestratorTimeout)
        monkeypatch.setattr(handler_module, "get_sync_service", lambda *args, **kwargs: MagicMock())

        message = DummyIncomingMessage(body=json.dumps(valid_payload).encode())
        await handler.handle(message)

        assert message.acked == 1
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "transient_exception"

    @pytest.mark.asyncio
    async def test_handle_client_error_4xx(self, monkeypatch, handler, valid_payload):
        import src.consumers.handler as handler_module

        monkeypatch.setattr(handler_module, "async_session", lambda: DummySessionContext())
        monkeypatch.setattr(handler_module, "SyncRecordRepository", DummyRepo)
        monkeypatch.setattr(handler_module, "SyncOrchestrator", DummyOrchestratorClientError)
        monkeypatch.setattr(handler_module, "get_sync_service", lambda *args, **kwargs: MagicMock())

        message = DummyIncomingMessage(body=json.dumps(valid_payload).encode())
        await handler.handle(message)

        assert message.acked == 1
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "client_error"

    @pytest.mark.asyncio
    async def test_handle_server_error_5xx(self, monkeypatch, handler, valid_payload):
        import src.consumers.handler as handler_module

        monkeypatch.setattr(handler_module, "async_session", lambda: DummySessionContext())
        monkeypatch.setattr(handler_module, "SyncRecordRepository", DummyRepo)
        monkeypatch.setattr(handler_module, "SyncOrchestrator", DummyOrchestratorServerError)
        monkeypatch.setattr(handler_module, "get_sync_service", lambda *args, **kwargs: MagicMock())

        message = DummyIncomingMessage(body=json.dumps(valid_payload).encode())
        await handler.handle(message)

        assert message.acked == 1
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "server_error"

    @pytest.mark.asyncio
    async def test_handle_request_error_goes_to_retry(self, monkeypatch, handler, valid_payload):
        import src.consumers.handler as handler_module

        class DummyOrchestratorRequestError:
            def __init__(self, repo):
                self.repo = repo

            async def execute(self, **kwargs):
                raise httpx.RequestError("conn failed", request=httpx.Request("GET", "https://example.com"))

        monkeypatch.setattr(handler_module, "async_session", lambda: DummySessionContext())
        monkeypatch.setattr(handler_module, "SyncRecordRepository", DummyRepo)
        monkeypatch.setattr(handler_module, "SyncOrchestrator", DummyOrchestratorRequestError)
        monkeypatch.setattr(handler_module, "get_sync_service", lambda *args, **kwargs: MagicMock())

        message = DummyIncomingMessage(body=json.dumps(valid_payload).encode())
        await handler.handle(message)

        assert message.acked == 1
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "transient_exception"

    @pytest.mark.asyncio
    async def test_handle_unexpected_exception_goes_to_retry(self, monkeypatch, handler, valid_payload):
        import src.consumers.handler as handler_module

        class DummyOrchestratorUnexpected:
            def __init__(self, repo):
                self.repo = repo

            async def execute(self, **kwargs):
                raise RuntimeError("unexpected")

        monkeypatch.setattr(handler_module, "async_session", lambda: DummySessionContext())
        monkeypatch.setattr(handler_module, "SyncRecordRepository", DummyRepo)
        monkeypatch.setattr(handler_module, "SyncOrchestrator", DummyOrchestratorUnexpected)
        monkeypatch.setattr(handler_module, "get_sync_service", lambda *args, **kwargs: MagicMock())

        message = DummyIncomingMessage(body=json.dumps(valid_payload).encode())
        await handler.handle(message)

        assert message.acked == 1
        assert len(handler._dlq.published) == 1
        assert handler._dlq.published[0]["reason"] == "unexpected_exception"


class TestMessageHandlerDispatch:
    """Тесты метода _dispatch."""

    @pytest.mark.asyncio
    async def test_dispatch_create(self, handler):
        service = AsyncMock()
        service.create = AsyncMock(return_value=SyncResponse(success=True))
        msg = RabbitMessage(entity_type="organization", action="create", payload={"id": 1})
        result = await handler._dispatch(service, msg)
        service.create.assert_awaited_once_with({"id": 1})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_dispatch_update(self, handler):
        service = AsyncMock()
        service.update = AsyncMock(return_value=SyncResponse(success=True))
        msg = RabbitMessage(entity_type="organization", action="update", object_id=1, payload={"name": "x"})
        result = await handler._dispatch(service, msg)
        service.update.assert_awaited_once_with(1, {"name": "x"})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_dispatch_update_payload_fallback(self, handler):
        service = AsyncMock()
        service.update = AsyncMock(return_value=SyncResponse(success=True))
        msg = RabbitMessage(entity_type="organization", action="update", object_id=1, payload={})
        result = await handler._dispatch(service, msg)
        service.update.assert_awaited_once_with(1, {"id": 1})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_dispatch_delete(self, handler):
        service = AsyncMock()
        service.delete = AsyncMock(return_value=SyncResponse(success=True))
        msg = RabbitMessage(entity_type="organization", action="delete", object_id=1)
        result = await handler._dispatch(service, msg)
        service.delete.assert_awaited_once_with(1)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_dispatch_get(self, handler):
        service = AsyncMock()
        service.get = AsyncMock(return_value=SyncResponse(success=True))
        msg = RabbitMessage(entity_type="organization", action="get", object_id=1)
        result = await handler._dispatch(service, msg)
        service.get.assert_awaited_once_with(1)
        assert result.success is True
