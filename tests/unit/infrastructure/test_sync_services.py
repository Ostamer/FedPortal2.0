"""Тесты сервисов синхронизации для всех сущностей.

Проверяем CRUD операции, префиксные ID, валидацию данных и маппинг.
"""
import pytest
from unittest.mock import AsyncMock

from src.services.sync_services import (
    ActivitySyncService,
    ClassicSyncService,
    EventSyncService,
)


@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.send = AsyncMock(return_value={
        "http_status_code": 200,
        "success": True,
        "data": {"id": 1},
    })
    return client


@pytest.fixture
def mock_formatter():
    formatter = AsyncMock()
    formatter.validate = lambda data: (True, None)
    formatter.format = lambda data: {**data, "formatted": True}
    return formatter


class TestClassicSyncService:
    """Тесты ClassicSyncService (organization, department, order, program-group, certificate, parents)."""

    @pytest.fixture
    def service(self, mock_client, mock_formatter):
        return ClassicSyncService(
            entity_type="organization",
            endpoint="organization",
            client=mock_client,
            formatter=mock_formatter,
        )

    @pytest.mark.asyncio
    async def test_create_success(self, service, mock_client, sample_organization_payload):
        result = await service.create(sample_organization_payload)
        assert result.success is True
        assert result.http_status_code == 200
        mock_client.send.assert_awaited_once()
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["endpoint"] == "organization"
        assert call_kwargs["json_data"]["formatted"] is True

    @pytest.mark.asyncio
    async def test_create_validation_fails_with_details(self, service, sample_organization_payload):
        service.formatter.validate = lambda data: (False, [{"loc": ["name"], "msg": "Field required", "input": None}])
        result = await service.create(sample_organization_payload)
        assert result.success is False
        assert result.http_status_code == 400
        assert result.message == "Validation failed"
        assert result.errors is not None
        assert "validation_errors" in result.errors
        assert len(result.errors["validation_errors"]) == 1
        assert result.errors["validation_errors"][0]["field"] == "name"

    @pytest.mark.asyncio
    async def test_update_success(self, service, mock_client, sample_organization_payload):
        result = await service.update(1, sample_organization_payload)
        assert result.success is True
        mock_client.send.assert_awaited_once()
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "PUT"
        assert call_kwargs["concrete_id"] == 1

    @pytest.mark.asyncio
    async def test_update_validation_fails_with_details(self, service, sample_organization_payload):
        service.formatter.validate = lambda data: (
            False,
            [
                {"loc": ["status"], "msg": "Invalid value", "input": 999},
                {"loc": ["legal_form"], "msg": "Invalid value", "input": "Unknown"},
            ],
        )
        result = await service.update(1, sample_organization_payload)
        assert result.success is False
        assert result.http_status_code == 400
        assert result.message == "Validation failed"
        assert result.errors is not None
        assert "validation_errors" in result.errors
        assert len(result.errors["validation_errors"]) == 2
        assert result.errors["validation_errors"][0]["field"] == "status"
        assert result.errors["validation_errors"][1]["field"] == "legal_form"

    @pytest.mark.asyncio
    async def test_delete_success(self, service, mock_client):
        result = await service.delete(1)
        assert result.success is True
        mock_client.send.assert_awaited_once()
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "DELETE"
        assert call_kwargs["concrete_id"] == 1

    @pytest.mark.asyncio
    async def test_get_success(self, service, mock_client):
        result = await service.get(1)
        assert result.success is True
        mock_client.send.assert_awaited_once()
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "GET"
        assert call_kwargs["concrete_id"] == 1

    @pytest.mark.asyncio
    async def test_client_error_response(self, mock_client, mock_formatter):
        mock_client.send = AsyncMock(return_value={
            "http_status_code": 500,
            "success": False,
            "message": "Internal error",
        })
        service = ClassicSyncService(
            entity_type="department",
            endpoint="department",
            client=mock_client,
            formatter=mock_formatter,
        )
        result = await service.get(1)
        assert result.success is False
        assert result.http_status_code == 500
        assert result.message == "Internal error"


class TestEventSyncService:
    """Тесты EventSyncService — использует префикс '2' для update/delete/get."""

    @pytest.fixture
    def service(self, mock_client, mock_formatter):
        return EventSyncService(
            entity_type="event",
            endpoint="event",
            client=mock_client,
            formatter=mock_formatter,
        )

    @pytest.mark.asyncio
    async def test_create_no_prefix(self, service, mock_client, sample_event_payload):
        await service.create(sample_event_payload)
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "POST"
        assert "concrete_id" not in call_kwargs or call_kwargs.get("concrete_id") is None

    @pytest.mark.asyncio
    async def test_update_uses_prefix_2(self, service, mock_client, sample_event_payload):
        await service.update(123, sample_event_payload)
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "PUT"
        assert call_kwargs["concrete_id"] == "2123"

    @pytest.mark.asyncio
    async def test_delete_uses_prefix_2(self, service, mock_client):
        await service.delete(456)
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "DELETE"
        assert call_kwargs["concrete_id"] == "2456"

    @pytest.mark.asyncio
    async def test_get_uses_prefix_2(self, service, mock_client):
        await service.get(789)
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "GET"
        assert call_kwargs["concrete_id"] == "2789"

    @pytest.mark.asyncio
    async def test_prefixed_id_method(self, service):
        assert service._resolve_id(0) == "20"
        assert service._resolve_id(99) == "299"


class TestActivitySyncService:
    """Тесты ActivitySyncService — использует префикс '1' для update/delete/get."""

    @pytest.fixture
    def service(self, mock_client, mock_formatter):
        return ActivitySyncService(
            entity_type="activity",
            endpoint="activity",
            client=mock_client,
            formatter=mock_formatter,
        )

    @pytest.mark.asyncio
    async def test_create_no_prefix(self, service, mock_client, sample_activity_payload):
        await service.create(sample_activity_payload)
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "POST"

    @pytest.mark.asyncio
    async def test_update_uses_prefix_1(self, service, mock_client, sample_activity_payload):
        await service.update(100, sample_activity_payload)
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "PUT"
        assert call_kwargs["concrete_id"] == "1100"

    @pytest.mark.asyncio
    async def test_delete_uses_prefix_1(self, service, mock_client):
        await service.delete(200)
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "DELETE"
        assert call_kwargs["concrete_id"] == "1200"

    @pytest.mark.asyncio
    async def test_get_uses_prefix_1(self, service, mock_client):
        await service.get(300)
        call_kwargs = mock_client.send.call_args.kwargs
        assert call_kwargs["method"] == "GET"
        assert call_kwargs["concrete_id"] == "1300"

    @pytest.mark.asyncio
    async def test_prefixed_id_method(self, service):
        assert service._resolve_id(5) == "15"
        assert service._resolve_id(42) == "142"


class TestBaseSyncServiceInterface:
    """Тесты, что базовый класс выбрасывает NotImplementedError."""

    @pytest.mark.asyncio
    async def test_base_create_not_implemented(self):
        from src.services.sync_services import BaseSyncService
        base = BaseSyncService()
        with pytest.raises(NotImplementedError):
            await base.create({})

    @pytest.mark.asyncio
    async def test_base_update_not_implemented(self):
        from src.services.sync_services import BaseSyncService
        base = BaseSyncService()
        with pytest.raises(NotImplementedError):
            await base.update(1, {})

    @pytest.mark.asyncio
    async def test_base_delete_not_implemented(self):
        from src.services.sync_services import BaseSyncService
        base = BaseSyncService()
        with pytest.raises(NotImplementedError):
            await base.delete(1)

    @pytest.mark.asyncio
    async def test_base_get_not_implemented(self):
        from src.services.sync_services import BaseSyncService
        base = BaseSyncService()
        with pytest.raises(NotImplementedError):
            await base.get(1)
