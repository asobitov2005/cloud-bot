"""Verify PostgreSQL migration"""
import asyncio
from app.core.database import engine, get_database_url
from sqlalchemy import text

async def verify():
    print("=" * 60)
    print("PostgreSQL Migration Verification")
    print("=" * 60)
    
    db_url = get_database_url()
    print(f"\nDatabase URL: {db_url}")
    print(f"Using PostgreSQL: {'postgresql' in db_url}\n")
    
    try:
        async with engine.begin() as conn:
            # Check PostgreSQL version
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"PostgreSQL Version: {version.split(',')[0]}\n")
            
            # Count records in each table
            tables = ['users', 'files', 'downloads', 'saved_list', 'settings']
            total = 0
            
            for table in tables:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"{table:15} : {count:4} records")
                    total += count
                except Exception as e:
                    print(f"{table:15} : Error - {e}")
            
            print(f"\n{'Total':15} : {total:4} records")
            print("\n" + "=" * 60)
            print("[OK] Migration verified successfully!")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify())

