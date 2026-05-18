from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, Index, UniqueConstraint

from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.enum import EntityType


class SyncedRecord(Base):
    """Реестр успешно синхронизированных сущностей."""

    __tablename__ = 'synced_records'
    __table_args__ = (
        UniqueConstraint('entity_type', 'object_id', name='uq_synced_records_entity_type_object_id'),
        Index('ix_synced_records_entity_type', 'entity_type'),
        Index('ix_synced_records_last_sync_time', 'last_sync_time'),
    )


    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    object_id: Mapped[int]
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name='entity_type', create_type=False),
    )
    last_sync_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f'<SyncedRecord(entity={self.entity_type.value}, object_id={self.object_id})>'
