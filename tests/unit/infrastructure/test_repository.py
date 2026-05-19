"""Тесты репозитория SyncRecordRepository.

Проверяем CRUD операции с логами и реестром синхронизированных записей.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.enum import EntityType, SyncSource
from src.models.sync_log import SyncLog
from src.models.synced_record import SyncedRecord
from src.repositories.sync_record import SyncRecordRepository


@pytest.fixture
def mock_session():
    session = MagicMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()

    # Мок для execute — возвращаем scalar_one_or_none
    def make_result(record):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        return mock_result

    session.execute = AsyncMock(side_effect=lambda stmt: make_result(None))
    return session


@pytest.fixture
def repo(mock_session):
    return SyncRecordRepository(mock_session)


class TestSyncRecordRepositoryCreateLog:
    """Тесты создания лога."""

    @pytest.mark.asyncio
    async def test_create_log_adds_to_session(self, repo, mock_session):
        log = await repo.create_log({"entity_type": "organization", "action": "create"}, SyncSource.MANUAL)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()
        assert isinstance(log, SyncLog)
        assert log.request_data == {"entity_type": "organization", "action": "create"}
        assert log.response_data is None
        assert log.source == SyncSource.MANUAL


class TestSyncRecordRepositoryUpdateLog:
    """Тесты обновления лога."""

    @pytest.mark.asyncio
    async def test_update_log_sets_response_data(self, repo):
        log = SyncLog(request_data={}, response_data=None, source=SyncSource.MANUAL)
        await repo.update_log(log, {"http_status_code": 200, "success": True})
        assert log.response_data == {"http_status_code": 200, "success": True}


class TestSyncRecordRepositoryCommitRollback:
    """Тесты транзакций."""

    @pytest.mark.asyncio
    async def test_commit(self, repo, mock_session):
        await repo.commit()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rollback(self, repo, mock_session):
        await repo.rollback()
        mock_session.rollback.assert_awaited_once()


class TestSyncRecordRepositoryUpsert:
    """Тесты upsert в реестр."""

    @pytest.mark.asyncio
    async def test_upsert_creates_new_record(self, repo, mock_session):
        await repo.upsert(EntityType.ORGANIZATION, 1)
        mock_session.add.assert_called_once()
        added = mock_session.add.call_args[0][0]
        assert isinstance(added, SyncedRecord)
        assert added.entity_type == EntityType.ORGANIZATION
        assert added.object_id == 1

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_record(self, repo, mock_session):
        existing = SyncedRecord(entity_type=EntityType.DEPARTMENT, object_id=5)
        existing.last_sync_time = datetime(2020, 1, 1, tzinfo=timezone.utc)

        def make_result(_):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = existing
            return mock_result

        mock_session.execute = AsyncMock(side_effect=make_result)

        await repo.upsert(EntityType.DEPARTMENT, 5)
        assert existing.last_sync_time > datetime(2020, 1, 1, tzinfo=timezone.utc)
        mock_session.add.assert_not_called()


class TestSyncRecordRepositoryDelete:
    """Тесты удаления из реестра."""

    @pytest.mark.asyncio
    async def test_delete_existing_record(self, repo, mock_session):
        existing = SyncedRecord(entity_type=EntityType.ORDER, object_id=10)

        def make_result(_):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = existing
            return mock_result

        mock_session.execute = AsyncMock(side_effect=make_result)

        await repo.delete(EntityType.ORDER, 10)
        mock_session.delete.assert_awaited_once_with(existing)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_record(self, repo, mock_session):
        await repo.delete(EntityType.EVENT, 999)
        mock_session.delete.assert_not_awaited()


class TestSyncRecordRepositoryGetRecord:
    """Тесты внутреннего метода _get_record."""

    @pytest.mark.asyncio
    async def test_get_record_returns_none_when_not_found(self, repo, mock_session):
        result = await repo._get_record(EntityType.ACTIVITY, 1)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_record_returns_record_when_found(self, repo, mock_session):
        existing = SyncedRecord(entity_type=EntityType.CERTIFICATE, object_id=7)

        def make_result(_):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = existing
            return mock_result

        mock_session.execute = AsyncMock(side_effect=make_result)

        result = await repo._get_record(EntityType.CERTIFICATE, 7)
        assert result is existing
