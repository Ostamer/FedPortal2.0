"""add sync log source

Revision ID: 003
Revises: 002
Create Date: 2026-05-19 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    exists = bind.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'syncsource'")
    ).scalar()
    if not exists:
        bind.execute(sa.text(
            "CREATE TYPE syncsource AS ENUM ('manual', 'main_queue', 'dlq_retry')"
        ))
    op.add_column(
        'sync_logs',
        sa.Column(
            'source',
            postgresql.ENUM('manual', 'main_queue', 'dlq_retry', name='syncsource', create_type=False),
            nullable=False,
            server_default='manual'
        ),
    )
    op.alter_column('sync_logs', 'source', server_default=None)

def downgrade() -> None:
    op.drop_column('sync_logs', 'source')
    op.get_bind().execute(sa.text("DROP TYPE IF EXISTS syncsource"))
