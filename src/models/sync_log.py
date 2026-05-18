from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


from src.models.base import Base


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


    def __repr__(self):
        return f"<SyncLog(id={self.id}, created_at={self.created_at})>"