
import sys
import os
from sqlmodel import Session, select, text
from sqlalchemy import create_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.models.user import User, Role, UserRole

engine = create_engine(str(settings.DATABASE_URI))

def debug_user():
    email = "admin@example.com" # Assuming default admin email, or I should list all users
    
    with Session(engine) as session:
        print(f"Checking users in DB: {settings.DATABASE_URI}")
        
        # 1. List all users and their status
        users = session.exec(select(User)).all()
        print(f"Total Users: {len(users)}")
        for u in users:
            print(f"User: {u.id} | {u.email} | Active: {u.is_active} | Verified: {u.is_verified} | Roles: {len(u.roles)}")
            
            # Check roles manually via UserRole table to be sure
            user_roles = session.exec(select(UserRole).where(UserRole.user_id == u.id)).all()
            for ur in user_roles:
                role = session.get(Role, ur.role_id)
                role_name = role.name if role else "UNKNOWN"
                print(f"  - Linked to Role ID: {ur.role_id} ({role_name})")

        # 2. List all roles
        roles = session.exec(select(Role)).all()
        print(f"\nTotal Roles: {len(roles)}")
        for r in roles:
            print(f"Role: {r.id} | {r.name}")

if __name__ == "__main__":
    debug_user()
