from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SyncRequest(BaseModel):
    """Запрос на синхронизацию через REST API."""
    action: str
    entity_type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    concrete_id: Optional[int] = None


class SyncResponse(BaseModel):
    """Ответ от сервиса синхронизации."""
    http_status_code: int = 200
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    errors: Optional[Dict[str, Any]] = None
    err_code: Optional[int | str] = None


class RabbitMessage(BaseModel):
    """Формат сообщения из RabbitMQ."""
    entity_type: str
    action: str
    object_id: Optional[int] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))