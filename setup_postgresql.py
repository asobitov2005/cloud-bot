"""Setup PostgreSQL database for migration"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

def setup_database():
    """Create database and user if they don't exist"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user='postgres',
            password='1122',
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'bot_db'")
        exists = cur.fetchone()
        
        if not exists:
            print("Creating database 'bot_db'...")
            cur.execute('CREATE DATABASE bot_db')
            print("[OK] Database 'bot_db' created")
        else:
            print("[OK] Database 'bot_db' already exists")
        
        # Check if user exists
        cur.execute("SELECT 1 FROM pg_user WHERE usename = 'bot_user'")
        user_exists = cur.fetchone()
        
        if not user_exists:
            print("Creating user 'bot_user'...")
            cur.execute("CREATE USER bot_user WITH PASSWORD '1122'")
            print("[OK] User 'bot_user' created")
        else:
            print("[OK] User 'bot_user' already exists")
        
        # Grant privileges
        cur.execute("GRANT ALL PRIVILEGES ON DATABASE bot_db TO bot_user")
        print("[OK] Privileges granted")
        
        # Connect to bot_db to grant schema privileges
        conn.close()
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user='postgres',
            password='1122',
            database='bot_db'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("GRANT ALL ON SCHEMA public TO bot_user")
        cur.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO bot_user")
        print("[OK] Schema privileges granted")
        
        cur.close()
        conn.close()
        print("\n[OK] PostgreSQL setup complete!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Connection error: {e}")
        print("\nPlease ensure PostgreSQL is running on port 5433")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)

