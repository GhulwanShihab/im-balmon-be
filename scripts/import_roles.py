
import sys
import os
import json
from sqlalchemy import create_engine, text
from sqlmodel import Session

# Add parent directory to path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.models.user import Role, UserRole

# Create sync engine
engine = create_engine(str(settings.DATABASE_URI))

def import_roles():
    input_file = os.path.join(os.path.dirname(__file__), "..", "data_backup.json")
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, "r") as f:
        data = json.load(f)

    with Session(engine) as session:
        # 1. Import Roles
        print("Importing Roles...")
        for item in data.get("roles", []):
            existing = session.get(Role, item["id"])
            if not existing:
                try:
                    obj = Role.model_validate(item)
                    session.add(obj)
                    session.commit()
                    print(f"Added Role {item['name']}")
                except Exception as e:
                    print(f"Failed to add Role {item['name']}: {e}")
                    session.rollback()
        print("Roles committed.")

        # 2. Import User Roles
        print("Importing User Roles...")
        for item in data.get("user_roles", []):
            existing = session.get(UserRole, item["id"])
            if not existing:
                try:
                    obj = UserRole.model_validate(item)
                    session.add(obj)
                    session.commit()
                    print(f"Added UserRole {item['id']}")
                except Exception as e:
                    print(f"Failed to add UserRole {item['id']}: {e}")
                    session.rollback()
        print("User Roles committed.")
        
        # Reset sequences
        for table in ["roles", "user_roles"]:
            try:
                sql = text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id)+1, 1), false) FROM {table};")
                session.exec(sql)
                session.commit()
            except Exception as e:
                print(f"Warning: Could not reset sequence for {table}: {e}")

if __name__ == "__main__":
    import_roles()
