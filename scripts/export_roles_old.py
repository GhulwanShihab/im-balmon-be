
import sys
import os
import json
from sqlmodel import Session, select
from sqlalchemy import create_engine

# Add parent directory to path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.models.user import Role, UserRole

# Connect to OLD database explicitly
# Assuming same credentials, just different DB name
old_db_url = str(settings.DATABASE_URI).rsplit("/", 1)[0] + "/im-balmon"
engine = create_engine(old_db_url)

def export_roles():
    print(f"Exporting roles from: {old_db_url}")
    
    # Load existing data_backup.json to preserve other data
    output_file = os.path.join(os.path.dirname(__file__), "..", "data_backup.json")
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            data = json.load(f)
    else:
        print("Warning: data_backup.json not found, creating new.")
        data = {}

    with Session(engine) as session:
        # 1. Roles
        print("Exporting Roles...")
        roles = session.exec(select(Role)).all()
        data["roles"] = [role.model_dump() for role in roles]
        print(f"Found {len(roles)} roles.")

        # 2. User Roles
        print("Exporting User Roles...")
        user_roles = session.exec(select(UserRole)).all()
        data["user_roles"] = [ur.model_dump() for ur in user_roles]
        print(f"Found {len(user_roles)} user roles.")
        
    with open(output_file, "w") as f:
        json.dump(data, f, default=str, indent=2)
    
    print(f"Roles exported successfully to {output_file}")

if __name__ == "__main__":
    export_roles()
