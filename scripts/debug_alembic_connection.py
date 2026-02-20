
import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings

from sqlalchemy import engine_from_config, pool

print(f"URI from settings: {settings.DATABASE_URI}")
config_dict = {"sqlalchemy.url": str(settings.DATABASE_URI)}
engine = engine_from_config(config_dict, prefix="sqlalchemy.", poolclass=pool.NullPool)

print("Attempting connection with engine_from_config...")
try:
    with engine.connect() as conn:
        print("Connected successfully!")
        result = conn.execute(text("SELECT current_database()"))
        print(f"Current database: {result.scalar()}")
except Exception as e:
    print(f"Connection failed: {e}")
