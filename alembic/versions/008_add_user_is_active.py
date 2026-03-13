"""Add is_active and deactivated_at to users table

Revision ID: 008
Revises: 007
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_active column (default True for all existing users)
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('deactivated_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('users', 'deactivated_at')
    op.drop_column('users', 'is_active')
