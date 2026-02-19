"""fix_enum_to_varchar

Revision ID: ae8ce0f5f155
Revises: 5fdc72a40013
Create Date: 2026-02-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ae8ce0f5f155'
down_revision: Union[str, None] = '5fdc72a40013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert device_condition from ENUM to VARCHAR in devices table
    op.execute(
        "ALTER TABLE devices ALTER COLUMN device_condition TYPE VARCHAR(50) USING device_condition::text"
    )
    
    # Convert device_condition from ENUM to VARCHAR in device_children table
    op.execute(
        "ALTER TABLE device_children ALTER COLUMN device_condition TYPE VARCHAR(50) USING device_condition::text"
    )
    
    # Drop old ENUM types after all columns have been converted
    op.execute("DROP TYPE IF EXISTS devicecondition CASCADE")
    op.execute("DROP TYPE IF EXISTS devicestatus CASCADE")


def downgrade() -> None:
    pass
