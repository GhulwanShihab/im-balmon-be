"""fix_inconsistent_device_status

Revision ID: d8bc5e81e3c6
Revises: 626a4c6af4a8
Create Date: 2026-04-24 12:28:32.708717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'd8bc5e81e3c6'
down_revision: Union[str, None] = '626a4c6af4a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Perbaiki status perangkat yang tidak konsisten: perangkat yang sedang dipinjam
    # tetapi statusnya tercatat sebagai 'TERSEDIA' karena bug logika pengembalian child.
    op.execute("""
        UPDATE devices
        SET device_status = 'DIPINJAM', updated_at = CURRENT_TIMESTAMP
        WHERE id IN (
            SELECT dli.device_id
            FROM device_loan_items dli
            JOIN device_loans dl ON dli.loan_id = dl.id
            WHERE dli.child_device_id IS NULL
              AND dl.status IN ('ACTIVE', 'OVERDUE')
              AND dl.deleted_at IS NULL
        )
        AND device_status != 'DIPINJAM'
    """)


def downgrade() -> None:
    pass
