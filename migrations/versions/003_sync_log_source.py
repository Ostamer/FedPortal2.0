"""add sync log source

Revision ID: 003
Revises: 002
Create Date: 2026-05-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sync_logs',
        sa.Column('source', sa.String(length=32), nullable=False, server_default='manual'),
    )
    op.alter_column('sync_logs', 'source', server_default=None)


def downgrade() -> None:
    op.drop_column('sync_logs', 'source')
