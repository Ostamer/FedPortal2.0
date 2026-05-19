"""
Репозиторий для SyncedRecord и SyncLog.
Вся работа с БД, связанная с синхронизацией, сосредоточена здесь.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.models.enum import EntityType
from src.models.sync_log import SyncLog
from src.models.synced_record import SyncedRecord

logger = get_logger(__name__)


class SyncRecordRepository:
    """CRUD-операции над SyncedRecord и SyncLog."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_log(self, request_data: dict) -> SyncLog:
        """Создать запись лога перед вызовом сервиса."""
        log = SyncLog(request_data=request_data, response_data=None)
        self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        logger.debug('sync_log_created', log_id=log.id)
        return log

    async def update_log(self, log: SyncLog, response_data: dict) -> None:
        """Записать результат вызова сервиса в лог."""
        log.response_data = response_data
        logger.debug('sync_log_updated', log_id=log.id)

    async def commit(self) -> None:
        """Зафиксировать транзакцию."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Откатить транзакцию."""
        await self._session.rollback()

    async def upsert(self, entity_type: EntityType, object_id: int) -> None:
        """Создать или обновить запись о синхронизированном объекте."""
        record = await self._get_record(entity_type, object_id)

        if record is None:
            record = SyncedRecord(entity_type=entity_type, object_id=object_id)
            self._session.add(record)
        else:
            record.last_sync_time = datetime.now(timezone.utc)

        logger.debug('synced_record_upserted', entity_type=entity_type, object_id=object_id)

    async def delete(self, entity_type: EntityType, object_id: int) -> None:
        """Удалить запись о синхронизированном объекте (после успешного delete)."""
        record = await self._get_record(entity_type, object_id)

        if record:
            await self._session.delete(record)
            logger.debug('synced_record_deleted', entity_type=entity_type, object_id=object_id)

    async def _get_record(self, entity_type: EntityType, object_id: int) -> SyncedRecord | None:
        """Получение записи об объекте на основе его id и типа сущности."""
        stmt = select(SyncedRecord).where(
            SyncedRecord.entity_type == entity_type,
            SyncedRecord.object_id == object_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
