"""add evidence_photo_url to condition_change_requests

Revision ID: a1b2c3d4e5f6
Revises: 3a80bbb3a1bb
Create Date: 2026-02-15 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '3a80bbb3a1bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'device_condition_change_requests',
        sa.Column('evidence_photo_url', sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('device_condition_change_requests', 'evidence_photo_url')
