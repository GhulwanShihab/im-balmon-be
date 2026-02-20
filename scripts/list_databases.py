
import sys
import os

# Add parent directory to path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from src.core.config import settings

# Connect to default postgres DB to list other DBs
# Assuming user/pass are correct from settings, just change db name
base_url = str(settings.DATABASE_URI).rsplit("/", 1)[0] + "/postgres"
engine = create_engine(base_url)

def list_dbs():
    try:
        with engine.connect() as conn:
            # Query to list all databases
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false;"))
            dbs = [row[0] for row in result]
            print("Available Databases:")
            for db in dbs:
                print(f"- {db}")
    except Exception as e:
        print(f"Error listing databases: {e}")

if __name__ == "__main__":
    list_dbs()
