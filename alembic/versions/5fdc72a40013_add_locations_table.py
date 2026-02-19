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
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'locations' in tables:
        # If table exists, existing logic: clean up and migrate columns
        op.execute("DELETE FROM locations")
        
        # Check constraints/indexes before dropping
        indexes = [i['name'] for i in inspector.get_indexes('locations')]
        if 'ix_locations_station_name' in indexes:
            op.drop_index('ix_locations_station_name', table_name='locations')
            
        columns = [c['name'] for c in inspector.get_columns('locations')]
        if 'room_name' in columns:
            op.drop_column('locations', 'room_name')
        if 'station_name' in columns:
            op.drop_column('locations', 'station_name')
            
        if 'name' not in columns:
            op.add_column('locations', sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
        if 'type' not in columns:
            op.add_column('locations', sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
            
        if 'ix_locations_name' not in indexes:
            op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)
            
    else:
        # If table doesn't exist, create it from scratch
        op.create_table('locations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)


def downgrade() -> None:
    # Downgrade logic - best effort
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'locations' in tables:
        columns = [c['name'] for c in inspector.get_columns('locations')]
        indexes = [i['name'] for i in inspector.get_indexes('locations')]
        
        if 'ix_locations_name' in indexes:
            op.drop_index(op.f('ix_locations_name'), table_name='locations')
            
        if 'type' in columns:
            op.drop_column('locations', 'type')
        if 'name' in columns:
            op.drop_column('locations', 'name')
            
        if 'station_name' not in columns:
            op.add_column('locations', sa.Column('station_name', sa.VARCHAR(), nullable=True)) # Nullable first to avoid errors
        if 'room_name' not in columns:
            op.add_column('locations', sa.Column('room_name', sa.VARCHAR(), nullable=True))
            
        if 'ix_locations_station_name' not in indexes:
            op.create_index('ix_locations_station_name', 'locations', ['station_name'], unique=False)
