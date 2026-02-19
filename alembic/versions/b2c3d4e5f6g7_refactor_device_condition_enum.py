"""Refactor device condition enum: RUSAK_RINGAN/RUSAK_BERAT -> RUSAK + MAINTENANCE

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-15 23:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add new enum values (must run outside transaction)
    op.execute("COMMIT")
    op.execute("ALTER TYPE devicecondition ADD VALUE IF NOT EXISTS 'RUSAK'")
    op.execute("ALTER TYPE devicecondition ADD VALUE IF NOT EXISTS 'MAINTENANCE'")
    
    # Start fresh transaction for data migration
    op.execute("BEGIN")
    
    # Step 2: Update existing data — cast to text for comparison to avoid enum issues
    # Device loan items
    op.execute("""
        UPDATE device_loan_items 
        SET condition_before = 'RUSAK'::devicecondition
        WHERE condition_before::text IN ('RUSAK_RINGAN', 'RUSAK_BERAT')
    """)
    op.execute("""
        UPDATE device_loan_items 
        SET condition_after = 'RUSAK'::devicecondition
        WHERE condition_after::text IN ('RUSAK_RINGAN', 'RUSAK_BERAT')
    """)

    # Condition change requests
    op.execute("""
        UPDATE device_condition_change_requests 
        SET old_condition = 'RUSAK'::devicecondition
        WHERE old_condition::text IN ('RUSAK_RINGAN', 'RUSAK_BERAT')
    """)
    op.execute("""
        UPDATE device_condition_change_requests 
        SET new_condition = 'RUSAK'::devicecondition
        WHERE new_condition::text IN ('RUSAK_RINGAN', 'RUSAK_BERAT')
    """)

    # Parent devices
    op.execute("""
        UPDATE devices 
        SET device_condition = 'RUSAK'::devicecondition
        WHERE device_condition::text IN ('RUSAK_RINGAN', 'RUSAK_BERAT')
    """)

    # Child devices
    op.execute("""
        UPDATE device_children 
        SET device_condition = 'RUSAK'::devicecondition
        WHERE device_condition::text IN ('RUSAK_RINGAN', 'RUSAK_BERAT')
    """)

    # Step 3: Recreate enum type without old values
    # First, alter all columns to text temporarily
    for table, col in [
        ("device_loan_items", "condition_before"),
        ("device_loan_items", "condition_after"),
        ("device_condition_change_requests", "old_condition"),
        ("device_condition_change_requests", "new_condition"),
        ("devices", "device_condition"),
        ("device_children", "device_condition"),
    ]:
        op.execute(f"""
            ALTER TABLE {table} 
            ALTER COLUMN {col} TYPE text USING {col}::text
        """)
        
        # ✅ FIX: Normalisasi data 'baik' menjadi 'BAIK' saat masih dalam format text
        op.execute(f"UPDATE {table} SET {col} = 'BAIK' WHERE {col} = 'baik'")
        op.execute(f"UPDATE {table} SET {col} = UPPER({col})")

    # Drop old enum and create clean one
    op.execute("DROP TYPE IF EXISTS devicecondition")
    op.execute("CREATE TYPE devicecondition AS ENUM ('BAIK', 'RUSAK', 'MAINTENANCE')")

    # Convert columns back to enum
    for table, col in [
        ("device_loan_items", "condition_before"),
        ("device_loan_items", "condition_after"),
        ("device_condition_change_requests", "old_condition"),
        ("device_condition_change_requests", "new_condition"),
        ("devices", "device_condition"),
        ("device_children", "device_condition"),
    ]:
        op.execute(f"""
            ALTER TABLE {table} 
            ALTER COLUMN {col} TYPE devicecondition USING {col}::devicecondition
        """)


def downgrade() -> None:
    # Convert all columns to text first
    for table, col in [
        ("device_loan_items", "condition_before"),
        ("device_loan_items", "condition_after"),
        ("device_condition_change_requests", "old_condition"),
        ("device_condition_change_requests", "new_condition"),
        ("devices", "device_condition"),
        ("device_children", "device_condition"),
    ]:
        op.execute(f"""
            ALTER TABLE {table} 
            ALTER COLUMN {col} TYPE text USING {col}::text
        """)

    # Convert RUSAK -> RUSAK_RINGAN, MAINTENANCE -> BAIK (best effort)
    op.execute("UPDATE devices SET device_condition = 'RUSAK_RINGAN' WHERE device_condition = 'RUSAK'")
    op.execute("UPDATE devices SET device_condition = 'BAIK' WHERE device_condition = 'MAINTENANCE'")
    op.execute("UPDATE device_children SET device_condition = 'RUSAK_RINGAN' WHERE device_condition = 'RUSAK'")
    op.execute("UPDATE device_children SET device_condition = 'BAIK' WHERE device_condition = 'MAINTENANCE'")
    op.execute("UPDATE device_loan_items SET condition_before = 'RUSAK_RINGAN' WHERE condition_before = 'RUSAK'")
    op.execute("UPDATE device_loan_items SET condition_after = 'RUSAK_RINGAN' WHERE condition_after = 'RUSAK'")
    op.execute("UPDATE device_condition_change_requests SET old_condition = 'RUSAK_RINGAN' WHERE old_condition = 'RUSAK'")
    op.execute("UPDATE device_condition_change_requests SET new_condition = 'RUSAK_RINGAN' WHERE new_condition = 'RUSAK'")

    # Drop new enum and create old one
    op.execute("DROP TYPE IF EXISTS devicecondition")
    op.execute("CREATE TYPE devicecondition AS ENUM ('BAIK', 'RUSAK_RINGAN', 'RUSAK_BERAT')")

    # Convert columns back to enum
    for table, col in [
        ("device_loan_items", "condition_before"),
        ("device_loan_items", "condition_after"),
        ("device_condition_change_requests", "old_condition"),
        ("device_condition_change_requests", "new_condition"),
        ("devices", "device_condition"),
        ("device_children", "device_condition"),
    ]:
        op.execute(f"""
            ALTER TABLE {table} 
            ALTER COLUMN {col} TYPE devicecondition USING {col}::devicecondition
        """)
