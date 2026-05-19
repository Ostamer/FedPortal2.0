"""initial

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENTITY_TYPE_VALUES = [
    'organization',
    'department',
    'order',
    'event',
    'activity',
    'program-group',
    'certificate',
    'program-group-financing-source',
    'parents',
]

from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    bind = op.get_bind()
    exists = bind.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'entity_type'")
    ).scalar()
    if not exists:
        bind.execute(sa.text(
            "CREATE TYPE entity_type AS ENUM ("
            "'organization', 'department', 'order', 'event', 'activity',"
            "'program-group', 'certificate', 'program-group-financing-source', 'parents'"
            ")"
        ))

    op.create_table(
        'sync_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('request_data', sa.JSON(), nullable=False),
        sa.Column('response_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sync_logs'))
    )
    op.create_table(
        'synced_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', postgresql.ENUM(
            *ENTITY_TYPE_VALUES,
            name='entity_type',
            create_type=False
        ), nullable=False),
        sa.Column('last_sync_time', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_synced_records')),
        sa.UniqueConstraint(
            'entity_type',
            'object_id',
            name='uq_synced_records_entity_type_object_id'
        )
    )

def downgrade() -> None:
    op.drop_table('synced_records')
    op.drop_table('sync_logs')
    op.get_bind().execute(sa.text("DROP TYPE IF EXISTS entity_type"))