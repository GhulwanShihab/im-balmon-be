
import sys
import os
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings

# Import all models to register them with SQLModel.metadata
from src.models.user import User
from src.models.location import Location
from src.models.perangkat import Device
from src.models.device_child import DeviceChild
from src.models.device_group import DeviceGroup, DeviceGroupItem
from src.models.loan import DeviceLoan, DeviceLoanItem, LoanHistory, DeviceConditionChangeRequest
from src.models.employee import Employee

def create_and_stamp():
    print(f"Creating schema on {settings.DATABASE_URI}...")
    engine = create_engine(str(settings.DATABASE_URI))
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    print("Schema created successfully!")
    
    # Stamp the database with alembic version
    # Head revision from 'alembic heads' output: 9c95afa8fd9f
    head_rev = "9c95afa8fd9f"
    
    print(f"Stamping database with revision {head_rev}...")
    with engine.connect() as conn:
        # Create alembic_version table if it doesn't exist (it shouldn't, but create_all might verify)
        # Actually create_all won't create it because it's not a SQLModel.
        # Alembic usually creates it automatically.
        
        # We need to create it manually
        conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) PRIMARY KEY)"))
        
        # Check if version exists
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current = result.scalar()
        if current:
            print(f"Database already at version {current}")
            if current != head_rev:
                print(f"Updating version to {head_rev}")
                conn.execute(text("UPDATE alembic_version SET version_num = :ver"), {"ver": head_rev})
        else:
            print(f"Inserting version {head_rev}")
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:ver)"), {"ver": head_rev})
        
        conn.commit()
    
    print("Database stamped successfully!")

if __name__ == "__main__":
    create_and_stamp()
