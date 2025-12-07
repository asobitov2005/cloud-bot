"""Add blocked_at field to users

Revision ID: e4f8c9a2b1d3
Revises: bc95e2ae559b
Create Date: 2025-12-07 17:39:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f8c9a2b1d3'
down_revision: Union[str, None] = 'bc95e2ae559b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add blocked_at column
    op.add_column('users', sa.Column('blocked_at', sa.DateTime(), nullable=True))
    
    # Backfill: Set blocked_at to joined_at for currently blocked users
    # This is an approximation since we don't have historical block data
    op.execute("""
        UPDATE users 
        SET blocked_at = joined_at 
        WHERE is_blocked = true AND blocked_at IS NULL
    """)


def downgrade() -> None:
    # Remove blocked_at column
    op.drop_column('users', 'blocked_at')
