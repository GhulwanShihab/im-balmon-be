
import sys
import os
from alembic.config import Config
from alembic import command

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings

def run_migrations():
    # Create Alembic configuration object
    alembic_cfg = Config("alembic.ini")
    
    # Override sqlalchemy.url with settings value
    db_url = str(settings.DATABASE_URI)
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    print(f"Running migrations on {db_url}...")
    
    try:
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migrations()
