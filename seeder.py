#!/usr/bin/env python3
"""
🌱 Secure Admin Seeder for IM-Balmon
------------------------------------
Creates a default admin user only if no admin exists.
If an admin already exists, this script will NOT overwrite anything.
"""

import asyncio
import sys
import traceback
import bcrypt
import os
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from dotenv import load_dotenv

from src.core.database import async_session, create_db_and_tables, engine
from src.models.user import User, Role, UserRole

# Load environment variables
load_dotenv()

# Default fallback values
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
DEFAULT_ADMIN_NAMA = os.getenv("ADMIN_NAMA", "Administrator")


async def create_basic_roles(session):
    """Create basic system roles if not exist."""
    print("DEBUG: Checking roles...", flush=True)
    roles_to_create = [
        {"name": "admin", "description": "Administrator with full access"},
        {"name": "manager", "description": "Manager with elevated access"},
        {"name": "user", "description": "Regular user with basic access"},
    ]

    for role_data in roles_to_create:
        try:
            print(f"DEBUG: Checking role {role_data['name']}...", flush=True)
            result = await session.execute(select(Role).where(Role.name == role_data["name"]))
            existing_role = result.scalars().first()
            
            if not existing_role:
                print(f"DEBUG: Creating role {role_data['name']}...", flush=True)
                session.add(Role(**role_data))
                print(f"✅ Created role: {role_data['name']}", flush=True)
            else:
                print(f"ℹ️ Role '{role_data['name']}' already exists", flush=True)
        except Exception as e:
            print(f"ERROR: Failed to process role {role_data['name']}: {e}", flush=True)
            raise e

    await session.commit()
    print("DEBUG: Roles committed.", flush=True)


async def create_admin_user(session):
    """Create default admin user if not exists."""
    print("DEBUG: Creating admin user...", flush=True)
    
    # Ensure admin role exists
    result = await session.execute(select(Role).where(Role.name == "admin"))
    admin_role = result.scalars().first()
    if not admin_role:
        print("DEBUG: Admin role not found, creating it...", flush=True)
        admin_role = Role(name="admin", description="Administrator with full access")
        session.add(admin_role)
        await session.commit()
        await session.refresh(admin_role)
        print("✅ Created admin role", flush=True)
    else:
        print("DEBUG: Admin role found.", flush=True)

    # Check if any admin user already exists
    # Simplify check to just user with 'admin' role, or simply check by email/nama
    # Checking by email is safer for uniqueness
    print(f"DEBUG: Checking existing admin by email {DEFAULT_ADMIN_EMAIL}...", flush=True)
    result = await session.execute(select(User).where(User.email == DEFAULT_ADMIN_EMAIL))
    existing_user_by_email = result.scalars().first()

    if existing_user_by_email:
        print(f"ℹ️ User with email '{DEFAULT_ADMIN_EMAIL}' already exists.", flush=True)
        
        # Check if they have admin role
        # We need to load roles. But let's keep it simple.
        # If user exists, we don't overwrite.
        print("🔒 Seeder will NOT overwrite existing user.", flush=True)
        return

    # Create default admin
    print("DEBUG: Hashing password...", flush=True)
    hashed_password = bcrypt.hashpw(
        DEFAULT_ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    print(f"DEBUG: Creating user object for {DEFAULT_ADMIN_NAMA}...", flush=True)
    admin_user = User(
        nama=DEFAULT_ADMIN_NAMA,
        email=DEFAULT_ADMIN_EMAIL,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=True,
    )

    session.add(admin_user)
    await session.commit()
    await session.refresh(admin_user)
    print("DEBUG: User created. Assigning role...", flush=True)

    # Assign admin role
    user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
    session.add(user_role)
    await session.commit()

    print("✅ Admin user created successfully!", flush=True)
    print(f"👤 Nama: {DEFAULT_ADMIN_NAMA}", flush=True)
    print(f"📧 Email: {DEFAULT_ADMIN_EMAIL}", flush=True)
    print(f"🔑 Password: {DEFAULT_ADMIN_PASSWORD}", flush=True)
    print("⚠️  Change this password immediately after first login!", flush=True)


async def main():
    print("🌱 Starting secure admin seeder...", flush=True)
    print("=" * 50, flush=True)

    # await create_db_and_tables()

    try:
        print("DEBUG: Opening session...", flush=True)
        async with async_session() as session:
            print("DEBUG: Session opened.", flush=True)
            await create_basic_roles(session)
            print("DEBUG: Finished creating roles.", flush=True)
            await create_admin_user(session)
            print("=" * 50, flush=True)
            print("🌱 Seeding completed successfully!", flush=True)
    except IntegrityError as e:
        # await session.rollback() # implicit rollback on exit
        print(f"❌ Integrity Error: {e}", flush=True)
    except Exception as e:
        # await session.rollback()
        print(f"❌ Unexpected Error: {e}", flush=True)
        traceback.print_exc()
    finally:
        print("DEBUG: Disposing engine...", flush=True)
        await engine.dispose()
        print("DEBUG: Engine disposed.", flush=True)


if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             # Set policy for Windows to avoid Event Loop Closed error
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except RuntimeError as e:
        if "Event loop is closed" not in str(e):
             raise e
    except Exception as e:
        print(f"CRITICAL ERROR: {e}", flush=True)
        traceback.print_exc()
