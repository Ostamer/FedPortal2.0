"""jsonb and indexes

Revision ID: 002
Revises: 001
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'sync_logs',
        'request_data',
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using='request_data::jsonb',
        existing_type=sa.JSON(),
        existing_nullable=False,
    )
    op.alter_column(
        'sync_logs',
        'response_data',
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using='response_data::jsonb',
        existing_type=sa.JSON(),
        existing_nullable=True,
    )

    op.create_index('ix_sync_logs_created_at', 'sync_logs', ['created_at'], unique=False)
    op.create_index('ix_synced_records_entity_type', 'synced_records', ['entity_type'], unique=False)
    op.create_index('ix_synced_records_last_sync_time', 'synced_records', ['last_sync_time'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_synced_records_last_sync_time', table_name='synced_records')
    op.drop_index('ix_synced_records_entity_type', table_name='synced_records')
    op.drop_index('ix_sync_logs_created_at', table_name='sync_logs')

    op.alter_column(
        'sync_logs',
        'response_data',
        type_=sa.JSON(),
        postgresql_using='response_data::json',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
    )
    op.alter_column(
        'sync_logs',
        'request_data',
        type_=sa.JSON(),
        postgresql_using='request_data::json',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
    )
