"""add_locations_table

Revision ID: 5fdc72a40013
Revises: b2c3d4e5f6g7
Create Date: 2026-02-16 21:44:16.208195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision: str = '5fdc72a40013'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old data and columns, add new schema
    op.execute("DELETE FROM locations")
    op.drop_index('ix_locations_station_name', table_name='locations')
    op.drop_column('locations', 'room_name')
    op.drop_column('locations', 'station_name')
    op.add_column('locations', sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.add_column('locations', sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_locations_name'), table_name='locations')
    op.drop_column('locations', 'type')
    op.drop_column('locations', 'name')
    op.add_column('locations', sa.Column('station_name', sa.VARCHAR(), nullable=False))
    op.add_column('locations', sa.Column('room_name', sa.VARCHAR(), nullable=False))
    op.create_index('ix_locations_station_name', 'locations', ['station_name'], unique=False)
