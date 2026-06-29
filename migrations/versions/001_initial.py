"""initial

Revision ID: 001_initial
Revises: 
Create Date: 2026-06-29 22:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create approval_requests table
    op.create_table(
        'approval_requests',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=100), nullable=False),
        sa.Column('source_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('reviewer_user_ids', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'idempotency_key', name='uq_workspace_idempotency_key')
    )
    op.create_index(op.f('ix_approval_requests_idempotency_key'), 'approval_requests', ['idempotency_key'], unique=False)
    op.create_index(op.f('ix_approval_requests_workspace_id'), 'approval_requests', ['workspace_id'], unique=False)

    # Create approval_logs table
    op.create_table(
        'approval_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('request_id', sa.Uuid(), nullable=False),
        sa.Column('actor_user_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('comment_or_reason', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['request_id'], ['approval_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approval_logs_request_id'), 'approval_logs', ['request_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_approval_logs_request_id'), table_name='approval_logs')
    op.drop_table('approval_logs')
    op.drop_index(op.f('ix_approval_requests_workspace_id'), table_name='approval_requests')
    op.drop_index(op.f('ix_approval_requests_idempotency_key'), table_name='approval_requests')
    op.drop_table('approval_requests')
