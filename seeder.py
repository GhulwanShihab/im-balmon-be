#!/usr/bin/env python3
"""
Admin user seeder script for IM-Balmon backend.
This script creates an admin user with all necessary roles and permissions.
"""

import asyncio
import bcrypt
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlalchemy import select as sql_select

from src.core.database import async_session, create_db_and_tables
from src.models.user import User, Role, UserRole
from src.utils.password import generate_secure_password


async def create_admin_user():
    """Create admin user with admin role."""
    
    # Create tables if they don't exist
    await create_db_and_tables()
    
    async with async_session() as session:
        try:
            # Check if admin role exists, create if not
            result = await session.execute(
                select(Role).where(Role.name == "admin")
            )
            admin_role = result.scalars().first()
            
            if not admin_role:
                admin_role = Role(
                    name="admin",
                    description="Administrator with full system access"
                )
                session.add(admin_role)
                await session.commit()
                await session.refresh(admin_role)
                print("✅ Admin role created")
            else:
                print("ℹ️  Admin role already exists")
            
            # Check if admin user exists
            result = await session.execute(
                select(User).where(User.email == "admin@im-balmon.com")
            )
            admin_user = result.scalars().first()
            
            if admin_user:
                print("⚠️  Admin user already exists with email: admin@im-balmon.com")
                return
            
            # Generate secure password
            password = generate_secure_password(16)
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create admin user
            admin_user = User(
                email="admin@im-balmon.com",
                hashed_password=hashed_password,
                first_name="System",
                last_name="Administrator",
                is_active=True,
                is_verified=True,
                force_password_change=True  # Force password change on first login
            )
            
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            # Assign admin role to user
            user_role = UserRole(
                user_id=admin_user.id,
                role_id=admin_role.id
            )
            session.add(user_role)
            await session.commit()
            
            print("✅ Admin user created successfully!")
            print(f"📧 Email: admin@im-balmon.com")
            print(f"🔑 Password: {password}")
            print("⚠️  Please save this password securely and change it on first login!")
            
        except IntegrityError as e:
            await session.rollback()
            print(f"❌ Error creating admin user: {e}")
        except Exception as e:
            await session.rollback()
            print(f"❌ Unexpected error: {e}")


async def create_basic_roles():
    """Create basic system roles."""
    
    roles_to_create = [
        {"name": "admin", "description": "Administrator with full system access"},
        {"name": "manager", "description": "Manager with device and user management access"},
        {"name": "user", "description": "Regular user with basic access"},
    ]
    
    async with async_session() as session:
        for role_data in roles_to_create:
            result = await session.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            if not result.scalars().first():
                role = Role(**role_data)
                session.add(role)
                print(f"✅ Created role: {role_data['name']}")
            else:
                print(f"ℹ️  Role '{role_data['name']}' already exists")
        
        await session.commit()


async def main():
    """Main seeder function."""
    print("🌱 Starting IM-Balmon admin user seeder...")
    print("=" * 50)
    
    try:
        # Create basic roles first
        await create_basic_roles()
        print()
        
        # Create admin user
        await create_admin_user()
        
        print("\n" + "=" * 50)
        print("🌱 Seeding completed!")
        
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)