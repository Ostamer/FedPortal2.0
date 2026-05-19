"""Тесты SyncOrchestrator.

Проверяем логирование, обновление реестра, commit/rollback, обработку ошибок.
"""
import pytest
from unittest.mock import AsyncMock

from src.models.enum import EntityType
from src.schemas.base import SyncResponse
from src.services.orchestrator import SyncOrchestrator


@pytest.fixture
def fake_repo():
    repo = AsyncMock()
    log_mock = AsyncMock()
    log_mock.id = 42
    repo.create_log = AsyncMock(return_value=log_mock)
    repo.update_log = AsyncMock()
    repo.commit = AsyncMock()
    repo.rollback = AsyncMock()
    repo.upsert = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def orchestrator(fake_repo):
    return SyncOrchestrator(fake_repo)


class TestSyncOrchestratorExecute:
    """Тесты метода execute."""

    @pytest.mark.asyncio
    async def test_execute_success_creates_log_and_commits(self, orchestrator, fake_repo):
        async def service_ok():
            return SyncResponse(http_status_code=200, success=True, data={"id": 1})

        result = await orchestrator.execute(
            entity_type=EntityType.ORGANIZATION,
            action="create",
            object_id=10,
            payload={"name": "Test"},
            service_coro=service_ok,
        )

        assert result.success is True
        fake_repo.create_log.assert_awaited_once()
        fake_repo.update_log.assert_awaited_once()
        fake_repo.commit.assert_awaited_once()
        fake_repo.upsert.assert_awaited_once_with(EntityType.ORGANIZATION, 10)

    @pytest.mark.asyncio
    async def test_execute_delete_removes_registry_record(self, orchestrator, fake_repo):
        async def service_ok():
            return SyncResponse(http_status_code=204, success=True)

        await orchestrator.execute(
            entity_type=EntityType.ORDER,
            action="delete",
            object_id=99,
            payload=None,
            service_coro=service_ok,
        )

        fake_repo.delete.assert_awaited_once_with(EntityType.ORDER, 99)
        fake_repo.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_create_uses_payload_id_when_object_id_none(self, orchestrator, fake_repo):
        async def service_ok():
            return SyncResponse(http_status_code=201, success=True)

        await orchestrator.execute(
            entity_type=EntityType.EVENT,
            action="create",
            object_id=None,
            payload={"id": 777, "name": "Event"},
            service_coro=service_ok,
        )

        fake_repo.upsert.assert_awaited_once_with(EntityType.EVENT, 777)

    @pytest.mark.asyncio
    async def test_execute_failure_rolls_back_and_reraises(self, orchestrator, fake_repo):
        async def service_fail():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            await orchestrator.execute(
                entity_type=EntityType.ACTIVITY,
                action="update",
                object_id=5,
                payload={"name": "Act"},
                service_coro=service_fail,
            )

        fake_repo.rollback.assert_awaited_once()
        fake_repo.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_no_upsert_when_unsuccessful(self, orchestrator, fake_repo):
        async def service_fail_http():
            return SyncResponse(http_status_code=400, success=False, message="bad request")

        result = await orchestrator.execute(
            entity_type=EntityType.DEPARTMENT,
            action="create",
            object_id=1,
            payload={"name": "Dep"},
            service_coro=service_fail_http,
        )

        assert result.success is False
        fake_repo.upsert.assert_not_awaited()
        fake_repo.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_request_data_contains_entity_and_action(self, orchestrator, fake_repo):
        async def service_ok():
            return SyncResponse(http_status_code=200, success=True)

        await orchestrator.execute(
            entity_type=EntityType.CERTIFICATE,
            action="get",
            object_id=50,
            payload=None,
            service_coro=service_ok,
        )

        call_args = fake_repo.create_log.call_args[0][0]
        assert call_args["entity_type"] == "certificate"
        assert call_args["action"] == "get"
        assert call_args["object_id"] == 50

    @pytest.mark.asyncio
    async def test_execute_request_data_omits_none_object_id(self, orchestrator, fake_repo):
        async def service_ok():
            return SyncResponse(http_status_code=200, success=True)

        await orchestrator.execute(
            entity_type=EntityType.ORGANIZATION,
            action="create",
            object_id=None,
            payload={"id": 1},
            service_coro=service_ok,
        )

        call_args = fake_repo.create_log.call_args[0][0]
        assert "object_id" not in call_args
        assert call_args["payload"] == {"id": 1}

    @pytest.mark.asyncio
    async def test_execute_request_data_omits_none_payload(self, orchestrator, fake_repo):
        async def service_ok():
            return SyncResponse(http_status_code=200, success=True)

        await orchestrator.execute(
            entity_type=EntityType.ORGANIZATION,
            action="delete",
            object_id=1,
            payload=None,
            service_coro=service_ok,
        )

        call_args = fake_repo.create_log.call_args[0][0]
        assert "payload" not in call_args


class TestSyncOrchestratorBuildResponsePayload:
    """Тесты вспомогательного метода build_response_payload."""

    def test_build_with_all_fields(self):
        response = SyncResponse(
            http_status_code=200,
            success=True,
            message="OK",
            data={"id": 1},
            errors={"field": "error"},
            err_code="ok",
        )
        payload = SyncOrchestrator.build_response_payload(response)
        assert payload == {
            "http_status_code": 200,
            "success": True,
            "data": {"id": 1},
            "message": "OK",
            "errors": {"field": "error"},
            "err_code": "ok",
        }

    def test_build_omits_none_fields(self):
        response = SyncResponse(http_status_code=204, success=True)
        payload = SyncOrchestrator.build_response_payload(response)
        assert "message" not in payload
        assert "data" not in payload
        assert "errors" not in payload
        assert "err_code" not in payload


class TestSyncOrchestratorLogError:
    """Тесты метода log_error."""

    @pytest.mark.asyncio
    async def test_log_error_creates_and_commits(self, orchestrator, fake_repo):
        await orchestrator.log_error(
            entity_type=EntityType.ORGANIZATION,
            action="create",
            object_id=1,
            payload={"name": "Test"},
            error_payload={"http_status_code": 500, "success": False, "message": "err"},
        )

        fake_repo.create_log.assert_awaited_once()
        fake_repo.update_log.assert_awaited_once()
        fake_repo.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_log_error_request_data_structure(self, orchestrator, fake_repo):
        await orchestrator.log_error(
            entity_type=EntityType.PROGRAM_GROUP,
            action="update",
            object_id=10,
            payload={"id": 10},
            error_payload={"success": False},
        )

        call_args = fake_repo.create_log.call_args[0][0]
        assert call_args["entity_type"] == "program-group"
        assert call_args["action"] == "update"
        assert call_args["object_id"] == 10
        assert call_args["payload"] == {"id": 10}
