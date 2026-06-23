"""add activity-order entity type

Revision ID: 005
Revises: 004
Create Date: 2026-06-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Новые значения enum
NEW_ENTITY_TYPES = [
    'activity-order',
]


def upgrade() -> None:
    """Добавить новые значения в enum entity_type."""
    bind = op.get_bind()

    for entity_type in NEW_ENTITY_TYPES:
        bind.execute(sa.text(
            f"ALTER TYPE entity_type ADD VALUE IF NOT EXISTS '{entity_type}'"
        ))


def downgrade() -> None:
    """
    Примечание: PostgreSQL не позволяет удалять значения из ENUM.
    Для отката потребуется пересоздание типа ENUM, что может быть
    разрушительной операцией. Эта функция оставлена пустой для безопасности.
    """
    pass
