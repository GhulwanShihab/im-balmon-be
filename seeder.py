#!/usr/bin/env python3
"""
🌱 Secure Admin Seeder for IM-Balmon
------------------------------------
Creates a default admin user only if no admin exists.
If an admin already exists, this script will NOT overwrite anything.
"""

import asyncio
import bcrypt
import os
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from dotenv import load_dotenv

from src.core.database import async_session, engine
from src.models.user import User, Role, UserRole

# Load environment variables (for ADMIN_EMAIL and ADMIN_PASSWORD)
load_dotenv()

# Default fallback values
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
DEFAULT_ADMIN_NAMA = os.getenv("ADMIN_NAMA", "Administrator")


async def create_basic_roles(session):
    """Create basic system roles if not exist."""
    roles_to_create = [
        {"name": "superadmin", "description": "Super Administrator with full access including admin management"},
        {"name": "admin", "description": "Administrator with full access"},
        {"name": "manager", "description": "Manager with elevated access"},
        {"name": "user", "description": "Regular user with basic access"},
    ]

    for role_data in roles_to_create:
        result = await session.execute(select(Role).where(Role.name == role_data["name"]))
        if not result.scalars().first():
            session.add(Role(**role_data))
            print(f"✅ Created role: {role_data['name']}")
        else:
            print(f"ℹ️ Role '{role_data['name']}' already exists")

    await session.commit()


async def create_admin_user(session):
    """Create default admin user if not exists."""
    # Ensure superadmin role exists
    result = await session.execute(select(Role).where(Role.name == "superadmin"))
    superadmin_role = result.scalars().first()
    if not superadmin_role:
        superadmin_role = Role(name="superadmin", description="Super Administrator with full access including admin management")
        session.add(superadmin_role)
        await session.commit()
        await session.refresh(superadmin_role)
        print("✅ Created superadmin role")

    # Check if any superadmin user already exists
    result = await session.execute(
        select(User).join(UserRole).join(Role).where(Role.name == "superadmin")
    )
    existing_admin = result.scalars().first()

    if existing_admin:
        print(f"ℹ️ Superadmin already exists with email: {existing_admin.email}")
        print("🔒 Seeder will NOT overwrite existing superadmin credentials.")
        return

    # Create default admin
    hashed_password = bcrypt.hashpw(
        DEFAULT_ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

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

    # Assign superadmin role
    user_role = UserRole(user_id=admin_user.id, role_id=superadmin_role.id)
    session.add(user_role)
    await session.commit()

    print("✅ Superadmin user created successfully!")
    print(f"👤 Nama: {DEFAULT_ADMIN_NAMA}")
    print(f"📧 Email: {DEFAULT_ADMIN_EMAIL}")
    print(f"🔑 Password: {DEFAULT_ADMIN_PASSWORD}")
    print(f"🛡️ Role: superadmin")
    print("⚠️  Change this password immediately after first login!")


async def main():
    print("🌱 Starting secure admin seeder...")
    print("=" * 50)

    # await create_db_and_tables()

    async with async_session() as session:
        try:
            await create_basic_roles(session)
            await create_admin_user(session)
            print("=" * 50)
            print("🌱 Seeding completed successfully!")
        except IntegrityError as e:
            await session.rollback()
            print(f"❌ Integrity Error: {e}")
        except Exception as e:
            await session.rollback()
            print(f"❌ Unexpected Error: {e}")
        finally:
            await engine.dispose()


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
