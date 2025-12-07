import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.models.crud import set_setting
from app.api.auth import get_password_hash

async def reset_admin(username, password):
    print(f"Resetting admin credentials in database...")
    print(f"Username: {username}")
    print(f"Password: {password}")
    
    async with AsyncSessionLocal() as db:
        # Update username
        await set_setting(db, "admin_username", username)
        
        # Update password hash
        password_hash = get_password_hash(password)
        await set_setting(db, "admin_password_hash", password_hash)
        
        print("Successfully updated admin credentials in database.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reset_admin_db.py <username> <password>")
        sys.exit(1)
        
    username = sys.argv[1]
    password = sys.argv[2]
    
    asyncio.run(reset_admin(username, password))
