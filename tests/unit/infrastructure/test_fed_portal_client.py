"""Тесты HTTP-клиента ExternalApiClient.

Проверяем обработку ответов, ошибки сети, парсинг JSON, заголовки и URL.
"""
import httpx
import pytest
from unittest.mock import AsyncMock

from src.clients.fed_portal import ExternalApiClient


@pytest.fixture
def client():
    return ExternalApiClient(
        base_url="https://fed.example.com",
        api_key="test-api-key",
        host="fed.example.com",
    )


@pytest.fixture
def mock_send(client):
    mock = AsyncMock()
    client._client.request = mock
    return mock


def build_response(status_code: int, content: bytes = b"", headers: dict | None = None) -> httpx.Response:
    req = httpx.Request("GET", "https://example.com")
    return httpx.Response(status_code=status_code, content=content, headers=headers or {}, request=req)


class TestExternalApiClientSend:
    """Тесты метода send."""

    @pytest.mark.asyncio
    async def test_success_json_response(self, client, mock_send):
        mock_send.return_value = build_response(
            200,
            content=b'{"id": 1, "name": "test"}',
            headers={"content-type": "application/json"},
        )
        result = await client.send(endpoint="organization", method="GET", concrete_id=1)
        assert result["success"] is True
        assert result["http_status_code"] == 200
        assert result["data"] == {"id": 1, "name": "test"}

    @pytest.mark.asyncio
    async def test_204_no_content(self, client, mock_send):
        mock_send.return_value = build_response(204)
        result = await client.send(endpoint="organization", method="DELETE", concrete_id=1)
        assert result["success"] is True
        assert result["http_status_code"] == 204
        assert result["data"] is None

    @pytest.mark.asyncio
    async def test_empty_200_body(self, client, mock_send):
        mock_send.return_value = build_response(200, content=b"")
        result = await client.send(endpoint="organization", method="GET", concrete_id=1)
        assert result["success"] is True
        assert result["http_status_code"] == 200
        assert result["data"] is None

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, client, mock_send):
        mock_send.return_value = build_response(
            200,
            content=b"not-json",
            headers={"content-type": "application/json"},
        )
        result = await client.send(endpoint="organization", method="GET", concrete_id=1)
        assert result["success"] is False
        assert result["err_code"] == "invalid_json_response"
        assert "raw_response" in result["data"]

    @pytest.mark.asyncio
    async def test_non_json_error_response(self, client, mock_send):
        mock_send.return_value = build_response(
            500,
            content=b"upstream failed",
            headers={"content-type": "text/plain"},
        )
        result = await client.send(endpoint="organization", method="GET", concrete_id=1)
        assert result["success"] is False
        assert result["err_code"] == "non_json_error_response"
        assert result["message"] == "upstream failed"
        assert result["data"] == {"raw_response": "upstream failed"}

    @pytest.mark.asyncio
    async def test_timeout_exception(self, client, mock_send):
        mock_send.side_effect = httpx.TimeoutException(
            "timeout", request=httpx.Request("GET", "https://example.com")
        )
        result = await client.send(endpoint="organization", method="GET")
        assert result["http_status_code"] == 504
        assert result["success"] is False
        assert result["err_code"] == "timeout"

    @pytest.mark.asyncio
    async def test_request_error(self, client, mock_send):
        mock_send.side_effect = httpx.RequestError(
            "connection failed", request=httpx.Request("GET", "https://example.com")
        )
        result = await client.send(endpoint="organization", method="GET")
        assert result["http_status_code"] == 502
        assert result["success"] is False
        assert result["err_code"] == "request_error"

    @pytest.mark.asyncio
    async def test_build_url_with_concrete_id(self, client, mock_send):
        mock_send.return_value = build_response(200, content=b"")
        await client.send(endpoint="organization", method="GET", concrete_id=123)
        call_args = mock_send.call_args
        assert call_args.kwargs["url"] == "https://fed.example.com/api/federal/v2/rest/organization/123"

    @pytest.mark.asyncio
    async def test_build_url_without_concrete_id(self, client, mock_send):
        mock_send.return_value = build_response(200, content=b"")
        await client.send(endpoint="organization", method="POST", json_data={"name": "test"})
        call_args = mock_send.call_args
        assert call_args.kwargs["url"] == "https://fed.example.com/api/federal/v2/rest/organization"

    @pytest.mark.asyncio
    async def test_headers_contain_authorization(self, client, mock_send):
        mock_send.return_value = build_response(200, content=b"")
        await client.send(endpoint="organization", method="GET")
        call_args = mock_send.call_args
        assert call_args.kwargs["headers"]["Authorization"] == "Bearer test-api-key"
        assert call_args.kwargs["headers"]["Host"] == "fed.example.com"

    @pytest.mark.asyncio
    async def test_params_contain_api_key(self, client, mock_send):
        mock_send.return_value = build_response(200, content=b"")
        await client.send(endpoint="organization", method="GET")
        call_args = mock_send.call_args
        assert call_args.kwargs["params"]["key"] == "test-api-key"

    @pytest.mark.asyncio
    async def test_json_data_passed(self, client, mock_send):
        mock_send.return_value = build_response(201, content=b"{}")
        payload = {"name": "Test Org"}
        await client.send(endpoint="organization", method="POST", json_data=payload)
        call_args = mock_send.call_args
        assert call_args.kwargs["json"] == payload

    @pytest.mark.asyncio
    async def test_str_concrete_id_in_url(self, client, mock_send):
        mock_send.return_value = build_response(200, content=b"")
        await client.send(endpoint="event", method="GET", concrete_id="2123")
        call_args = mock_send.call_args
        assert "event/2123" in call_args.kwargs["url"]


class TestExternalApiClientClose:
    """Тесты закрытия клиента."""

    @pytest.mark.asyncio
    async def test_close_calls_aclose(self, client):
        client._client.aclose = AsyncMock()
        await client.close()
        client._client.aclose.assert_awaited_once()
