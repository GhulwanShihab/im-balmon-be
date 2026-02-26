"""add superadmin role

Revision ID: b3c4d5e6f7g8
Revises: a2b3c4d5e6f7
Create Date: 2026-02-26 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7g8'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Insert superadmin role
    op.execute(
        "INSERT INTO roles (name, description, created_at, updated_at) "
        "VALUES ('superadmin', 'Super Administrator with full access including admin management', NOW(), NOW()) "
        "ON CONFLICT (name) DO NOTHING"
    )

    # 2. Get the superadmin role id and the first admin user, and assign superadmin role to them
    op.execute("""
        INSERT INTO user_roles (user_id, role_id, created_at, updated_at)
        SELECT ur.user_id, sr.id, NOW(), NOW()
        FROM user_roles ur
        JOIN roles ar ON ur.role_id = ar.id AND ar.name = 'admin'
        CROSS JOIN roles sr
        WHERE sr.name = 'superadmin'
        AND NOT EXISTS (
            SELECT 1 FROM user_roles ur2
            JOIN roles r2 ON ur2.role_id = r2.id
            WHERE ur2.user_id = ur.user_id AND r2.name = 'superadmin'
        )
        LIMIT 1
    """)


def downgrade() -> None:
    # Remove superadmin role assignments
    op.execute(
        "DELETE FROM user_roles WHERE role_id = (SELECT id FROM roles WHERE name = 'superadmin')"
    )
    # Remove superadmin role
    op.execute("DELETE FROM roles WHERE name = 'superadmin'")
