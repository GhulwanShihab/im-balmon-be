"""add cascade delete on user foreign keys

Revision ID: a2b3c4d5e6f7
Revises: c1aa42d7e220
Create Date: 2026-02-26 14:08:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'c1aa42d7e220'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # employees.user_id -> users.id CASCADE
    op.drop_constraint('employees_user_id_fkey', 'employees', type_='foreignkey')
    op.create_foreign_key('employees_user_id_fkey', 'employees', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # user_roles.user_id -> users.id CASCADE
    op.drop_constraint('user_roles_user_id_fkey', 'user_roles', type_='foreignkey')
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # password_reset_tokens.user_id -> users.id CASCADE
    op.drop_constraint('password_reset_tokens_user_id_fkey', 'password_reset_tokens', type_='foreignkey')
    op.create_foreign_key('password_reset_tokens_user_id_fkey', 'password_reset_tokens', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # mfa_backup_codes.user_id -> users.id CASCADE
    op.drop_constraint('mfa_backup_codes_user_id_fkey', 'mfa_backup_codes', type_='foreignkey')
    op.create_foreign_key('mfa_backup_codes_user_id_fkey', 'mfa_backup_codes', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Revert to original constraints without CASCADE
    op.drop_constraint('employees_user_id_fkey', 'employees', type_='foreignkey')
    op.create_foreign_key('employees_user_id_fkey', 'employees', 'users', ['user_id'], ['id'])

    op.drop_constraint('user_roles_user_id_fkey', 'user_roles', type_='foreignkey')
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'])

    op.drop_constraint('password_reset_tokens_user_id_fkey', 'password_reset_tokens', type_='foreignkey')
    op.create_foreign_key('password_reset_tokens_user_id_fkey', 'password_reset_tokens', 'users', ['user_id'], ['id'])

    op.drop_constraint('mfa_backup_codes_user_id_fkey', 'mfa_backup_codes', type_='foreignkey')
    op.create_foreign_key('mfa_backup_codes_user_id_fkey', 'mfa_backup_codes', 'users', ['user_id'], ['id'])
