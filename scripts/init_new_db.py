
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings

def create_database():
    # Connect to default 'postgres' database to create new db
    # Construct URI for 'postgres' db
    project_db = settings.POSTGRES_DB
    
    # settings.DATABASE_URI likely uses PROJECT_DB. We need to replace it.
    # Or just construct it manually
    user = settings.POSTGRES_USER
    password = settings.POSTGRES_PASSWORD
    host = settings.POSTGRES_SERVER
    port = settings.POSTGRES_PORT
    
    # Connect to 'postgres'
    db_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"
    
    engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
    
    target_db = "imbalmon"
    
    print(f"Checking if database '{target_db}' exists...")
    
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{target_db}'"))
        if result.scalar():
            print(f"Database '{target_db}' already exists.")
        else:
            print(f"Database '{target_db}' does not exist. Creating...")
            try:
                conn.execute(text(f"CREATE DATABASE {target_db}"))
                print(f"Database '{target_db}' created successfully.")
            except ProgrammingError as e:
                print(f"Error creating database: {e}")

    # Test connection to new DB
    print(f"Testing connection to {target_db}...")
    try:
        new_db_url = f"postgresql://{user}:{password}@{host}:{port}/{target_db}"
        new_engine = create_engine(new_db_url)
        with new_engine.connect() as conn:
            print(f"Successfully connected to {target_db}!")
    except Exception as e:
        print(f"Failed to connect to {target_db}: {e}")

if __name__ == "__main__":
    create_database()
