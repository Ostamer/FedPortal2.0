from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.enum import SyncSource


class SyncLog(Base):
    """Лог всех попыток синхронизации (аудит)."""

    __tablename__ = "sync_logs"
    __table_args__ = (
        Index('ix_sync_logs_created_at', 'created_at'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
    request_data: Mapped[dict] = mapped_column(JSONB)
    response_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    source: Mapped[SyncSource] = mapped_column(
        PgEnum(SyncSource, name='syncsource', create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=SyncSource.MANUAL
    )

    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id}, created_at={self.created_at})>"
