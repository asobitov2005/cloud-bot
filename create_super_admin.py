#!/usr/bin/env python3
"""
Create Super Admin User

This script creates a super admin user for the admin panel.
Run this after database migration.

Usage:
    python create_super_admin.py
"""
import asyncio
import sys
from getpass import getpass
from app.core.database import AsyncSessionLocal
from app.models.crud import create_admin_user, get_admin_by_username
from app.models.base import AdminRole
from app.api.auth import get_password_hash


async def create_super_admin():
    """Create super admin user interactively"""
    print("=" * 60)
    print("  CREATE SUPER ADMIN USER")
    print("=" * 60)
    print()
    
    # Get username
    while True:
        username = input("Enter username: ").strip()
        if len(username) < 3:
            print("❌ Username must be at least 3 characters long!")
            continue
        break
    
    # Get password
    while True:
        password = getpass("Enter password: ").strip()
        if len(password) < 6:
            print("❌ Password must be at least 6 characters long!")
            continue
        
        password_confirm = getpass("Confirm password: ").strip()
        if password != password_confirm:
            print("❌ Passwords do not match!")
            continue
        break
    
    # Get optional fields
    full_name = input("Enter full name (optional): ").strip() or None
    email = input("Enter email (optional): ").strip() or None
    
    print()
    print("-" * 60)
    print(f"Username: {username}")
    print(f"Full Name: {full_name or 'N/A'}")
    print(f"Email: {email or 'N/A'}")
    print(f"Role: SUPER ADMIN")
    print("-" * 60)
    
    confirm = input("\nCreate this super admin? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ Cancelled.")
        sys.exit(0)
    
    # Create admin user
    async with AsyncSessionLocal() as db:
        # Check if username already exists
        existing = await get_admin_by_username(db, username)
        if existing:
            print(f"\n❌ Error: Username '{username}' already exists!")
            sys.exit(1)
        
        # Hash password
        password_hash = get_password_hash(password)
        
        # Create super admin
        admin = await create_admin_user(
            db,
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            email=email,
            role=AdminRole.SUPER_ADMIN
        )
        
        print()
        print("=" * 60)
        print(f"✅ Super admin created successfully!")
        print(f"   ID: {admin.id}")
        print(f"   Username: {admin.username}")
        print(f"   Role: {admin.role.value}")
        print("=" * 60)
        print()
        print("🎉 You can now login to admin panel at:")
        print("   https://prime.testnest.uz/admin/login")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(create_super_admin())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
