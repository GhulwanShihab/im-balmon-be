"""add uuid to users table

Revision ID: c4d5e6f7g8h9
Revises: b3c4d5e6f7g8
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic
revision = 'c4d5e6f7g8h9'
down_revision = 'b3c4d5e6f7g8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add uuid column as nullable first
    op.add_column('users', sa.Column('uuid', sa.String(36), nullable=True))
    
    # Step 2: Generate UUID for existing users
    conn = op.get_bind()
    users = conn.execute(sa.text("SELECT id FROM users")).fetchall()
    for user in users:
        new_uuid = str(uuid.uuid4())
        conn.execute(
            sa.text("UPDATE users SET uuid = :uuid WHERE id = :id"),
            {"uuid": new_uuid, "id": user[0]}
        )
    
    # Step 3: Make it non-nullable and add unique index
    op.alter_column('users', 'uuid', nullable=False)
    op.create_unique_constraint('uq_users_uuid', 'users', ['uuid'])
    op.create_index('ix_users_uuid', 'users', ['uuid'])


def downgrade() -> None:
    op.drop_index('ix_users_uuid', table_name='users')
    op.drop_constraint('uq_users_uuid', 'users', type_='unique')
    op.drop_column('users', 'uuid')
