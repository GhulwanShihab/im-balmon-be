"""fix_loan_enums_to_varchar

Revision ID: 9c95afa8fd9f
Revises: ae8ce0f5f155
Create Date: 2026-02-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9c95afa8fd9f'
down_revision: Union[str, None] = 'ae8ce0f5f155'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Helper function to handle column update or creation
    def ensure_varchar_column(table_name, column_name, length=50, default_val=None):
        columns = [c['name'] for c in inspector.get_columns(table_name)]
        if column_name in columns:
            # Column exists, convert to VARCHAR
            # First drop default if exists to avoid issues
            op.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP DEFAULT")
            op.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE VARCHAR({length}) USING {column_name}::text")
        else:
            # Column missing (was dropped via cascade?), add it
            op.add_column(table_name, sa.Column(column_name, sa.String(length), nullable=True))
            if default_val:
                op.execute(f"UPDATE {table_name} SET {column_name} = '{default_val}' WHERE {column_name} IS NULL")

    # 1. device_loans table
    ensure_varchar_column('device_loans', 'status', 20, 'ACTIVE')

    # 2. device_loan_items table
    ensure_varchar_column('device_loan_items', 'condition_before', 50, 'BAIK')
    ensure_varchar_column('device_loan_items', 'condition_after', 50)

    # 3. loan_history table
    ensure_varchar_column('loan_history', 'old_status', 20)
    ensure_varchar_column('loan_history', 'new_status', 20)
    
    # 4. device_condition_change_requests table
    ensure_varchar_column('device_condition_change_requests', 'old_condition', 50)
    ensure_varchar_column('device_condition_change_requests', 'new_condition', 50)
    ensure_varchar_column('device_condition_change_requests', 'status', 20, 'PENDING')

    # 5. Drop the ENUM types if they still exist
    op.execute("DROP TYPE IF EXISTS loanstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS devicecondition CASCADE")
    op.execute("DROP TYPE IF EXISTS conditionchangestatus CASCADE")


def downgrade() -> None:
    # Not implementing downgrade for this as it's a structural fix to move away from DB-level ENUMs
    pass
