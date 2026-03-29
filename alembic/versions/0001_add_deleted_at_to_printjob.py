"""Add deleted_at to PrintJob

Revision ID: 0001
Revises:
Create Date: 2026-03-29 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'print_jobs' in tables:
        columns = [col['name'] for col in inspector.get_columns('print_jobs')]
        if 'deleted_at' not in columns:
            op.add_column('print_jobs', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    else:
        op.create_table('print_jobs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(), nullable=True),
            sa.Column('source', sa.String(), nullable=True),
            sa.Column('source_url', sa.String(), nullable=True),
            sa.Column('file_path', sa.String(), nullable=True),
            sa.Column('thumbnail_url', sa.String(), nullable=True),
            sa.Column('author', sa.String(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('status', sa.Enum('TO_BE_PRINTED', 'PRINT_IN_PROGRESS', 'PRINT_AGAIN', 'PRINTED', 'SKIPPED', 'DELETED', name='printstatus'), nullable=True),
            sa.Column('material_notes', sa.String(), nullable=True),
            sa.Column('timing_notes', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_print_jobs_id'), 'print_jobs', ['id'], unique=False)
        op.create_index(op.f('ix_print_jobs_source'), 'print_jobs', ['source'], unique=False)
        op.create_index(op.f('ix_print_jobs_title'), 'print_jobs', ['title'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    if 'print_jobs' in tables:
        columns = [col['name'] for col in inspector.get_columns('print_jobs')]
        if 'deleted_at' in columns:
            op.drop_column('print_jobs', 'deleted_at')
