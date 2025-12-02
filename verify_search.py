import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import async_session_maker
from app.models.crud import search_users, search_files, get_users_count, get_files_count

async def verify_search():
    print("Starting Search Verification...")
    
    async with async_session_maker() as db:
        # 1. Verify User Search
        print("\n--- Verifying User Search ---")
        total_users = await get_users_count(db)
        print(f"Total Users in DB: {total_users}")
        
        # Search for 'admin' (likely to exist)
        query = "admin"
        users = await search_users(db, query=query, limit=5)
        print(f"Search query: '{query}'")
        print(f"Found {len(users)} users:")
        for u in users:
            print(f" - ID: {u.id}, Username: {u.username}, Name: {u.full_name}")
            
        # 2. Verify File Search
        print("\n--- Verifying File Search ---")
        total_files = await get_files_count(db)
        print(f"Total Files in DB: {total_files}")
        
        # Search for common file extensions or terms
        query = "pdf" # Example query
        files = await search_files(db, query=query, limit=5)
        print(f"Search query: '{query}'")
        print(f"Found {len(files)} files:")
        for f in files:
            print(f" - ID: {f.id}, Title: {f.title}")

if __name__ == "__main__":
    try:
        asyncio.run(verify_search())
        print("\nVerification script finished successfully.")
    except Exception as e:
        print(f"\nError during verification: {e}")
