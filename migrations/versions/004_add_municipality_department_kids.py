"""add municipality, department, kids entity types

Revision ID: 004
Revises: 003
Create Date: 2026-05-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Новые значения enum
NEW_ENTITY_TYPES = [
    'municipality',
    'department',
    'kids',
]


def upgrade() -> None:
    """Добавить новые значения в enum entity_type."""
    bind = op.get_bind()
    
    # Добавляем новые значения в enum entity_type
    for entity_type in NEW_ENTITY_TYPES:
        bind.execute(sa.text(
            f"ALTER TYPE entity_type ADD VALUE IF NOT EXISTS '{entity_type}'"
        ))


def downgrade() -> None:
    """
    Примечание: PostgreSQL не позволяет удалять значения из ENUM.
    Для отката потребуется пересоздание типа ENUM, что может быть разрушительной операцией.
    Эта функция оставлена пустой для безопасности.
    """
    pass
