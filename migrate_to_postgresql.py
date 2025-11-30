"""
Migration script to transfer data from SQLite to PostgreSQL

Usage:
1. Install PostgreSQL and create database
2. Update .env with PostgreSQL credentials
3. Run: python migrate_to_postgresql.py
"""
import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.base import Base, User, File, Download, SavedList
from app.models.settings import Settings
try:
    from app.models.health import HealthCheck
except ImportError:
    HealthCheck = None
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_sqlite_engine():
    """Get SQLite engine (synchronous for data migration)"""
    sqlite_url = "sqlite:///./bot.db"
    return create_engine(sqlite_url, echo=False)


def get_postgres_engine():
    """Get PostgreSQL engine (synchronous for data migration)"""
    # Use provided credentials or settings
    postgres_host = 'localhost'
    postgres_port = 5433
    postgres_user = 'postgres'
    postgres_password = '1122'
    postgres_db = 'bot_db'
    
    # Override with settings if available
    if hasattr(settings, 'POSTGRES_HOST') and settings.POSTGRES_HOST:
        postgres_host = settings.POSTGRES_HOST
    if hasattr(settings, 'POSTGRES_PORT') and settings.POSTGRES_PORT:
        postgres_port = settings.POSTGRES_PORT
    if hasattr(settings, 'POSTGRES_USER') and settings.POSTGRES_USER:
        postgres_user = settings.POSTGRES_USER
    if hasattr(settings, 'POSTGRES_PASSWORD') and settings.POSTGRES_PASSWORD:
        postgres_password = settings.POSTGRES_PASSWORD
    if hasattr(settings, 'POSTGRES_DB') and settings.POSTGRES_DB:
        postgres_db = settings.POSTGRES_DB
    
    postgres_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    
    return create_engine(postgres_url, echo=False)


def migrate_table_data(source_session: Session, target_session: Session, 
                      source_model, target_model, table_name: str):
    """Migrate data from one table to another"""
    try:
        # Get all records from source
        source_records = source_session.query(source_model).all()
        
        if not source_records:
            logger.info(f"No data to migrate for {table_name}")
            return 0
        
        logger.info(f"Migrating {len(source_records)} records from {table_name}...")
        
        # Convert SQLAlchemy objects to dicts and insert into target
        migrated_count = 0
        for record in source_records:
            try:
                # Convert to dict, excluding SQLAlchemy internal attributes
                record_dict = {}
                for column in source_model.__table__.columns:
                    value = getattr(record, column.name)
                    record_dict[column.name] = value
                
                # Create new record in target database
                target_record = target_model(**record_dict)
                target_session.add(target_record)
                migrated_count += 1
            except Exception as e:
                logger.warning(f"Error migrating record {record.id} from {table_name}: {e}")
                continue
        
        target_session.commit()
        logger.info(f"✅ Migrated {migrated_count}/{len(source_records)} records from {table_name}")
        return migrated_count
        
    except Exception as e:
        target_session.rollback()
        logger.error(f"❌ Error migrating {table_name}: {e}")
        raise


def migrate_settings(source_session: Session, target_session: Session):
    """Migrate settings table"""
    try:
        source_settings = source_session.query(Settings).all()
        
        if not source_settings:
            logger.info("No settings to migrate")
            return 0
        
        logger.info(f"Migrating {len(source_settings)} settings...")
        
        migrated_count = 0
        for setting in source_settings:
            try:
                # Check if setting already exists in target
                existing = target_session.query(Settings).filter(
                    Settings.key == setting.key
                ).first()
                
                if existing:
                    existing.value = setting.value
                else:
                    target_session.add(Settings(key=setting.key, value=setting.value))
                
                migrated_count += 1
            except Exception as e:
                logger.warning(f"Error migrating setting {setting.key}: {e}")
                continue
        
        target_session.commit()
        logger.info(f"✅ Migrated {migrated_count} settings")
        return migrated_count
        
    except Exception as e:
        target_session.rollback()
        logger.error(f"❌ Error migrating settings: {e}")
        raise


def migrate_fsub_channels(source_session: Session, target_session: Session):
    """Migrate force subscribe channels (stored as JSON in settings)"""
    # Force subscribe channels are stored in settings, so they're already migrated
    # with the settings migration. This function is kept for compatibility.
    logger.info("Force subscribe channels are stored in settings (already migrated)")
    return 0


def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("SQLite to PostgreSQL Migration")
    logger.info("=" * 60)
    
    # Check PostgreSQL configuration
    try:
        postgres_engine = get_postgres_engine()
        # Test connection
        with postgres_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ PostgreSQL connection successful")
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        logger.error("\nPlease configure PostgreSQL in .env:")
        logger.error("POSTGRES_HOST=localhost")
        logger.error("POSTGRES_PORT=5432")
        logger.error("POSTGRES_USER=postgres")
        logger.error("POSTGRES_PASSWORD=your_password")
        logger.error("POSTGRES_DB=bot_db")
        sys.exit(1)
    
    # Check SQLite database exists
    sqlite_engine = get_sqlite_engine()
    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ SQLite database found")
    except Exception as e:
        logger.error(f"❌ SQLite database not found: {e}")
        sys.exit(1)
    
    # Create PostgreSQL tables
    logger.info("\nCreating PostgreSQL tables...")
    try:
        Base.metadata.create_all(postgres_engine)
        logger.info("✅ PostgreSQL tables created")
    except Exception as e:
        logger.error(f"❌ Error creating PostgreSQL tables: {e}")
        sys.exit(1)
    
    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()
    
    try:
        logger.info("\n" + "=" * 60)
        logger.info("Starting data migration...")
        logger.info("=" * 60 + "\n")
        
        # Migrate tables in order (respecting foreign keys)
        total_migrated = 0
        
        # 1. Users (no dependencies)
        total_migrated += migrate_table_data(
            sqlite_session, postgres_session, User, User, "users"
        )
        
        # 2. Files (no dependencies)
        total_migrated += migrate_table_data(
            sqlite_session, postgres_session, File, File, "files"
        )
        
        # 3. Downloads (depends on users and files)
        total_migrated += migrate_table_data(
            sqlite_session, postgres_session, Download, Download, "downloads"
        )
        
        # 4. SavedList (depends on users and files)
        total_migrated += migrate_table_data(
            sqlite_session, postgres_session, SavedList, SavedList, "saved_list"
        )
        
        # 5. Settings
        total_migrated += migrate_settings(sqlite_session, postgres_session)
        
        # 6. Force Subscribe Channels
        total_migrated += migrate_fsub_channels(sqlite_session, postgres_session)
        
        # 7. Health Checks (if exists)
        if HealthCheck:
            try:
                total_migrated += migrate_table_data(
                    sqlite_session, postgres_session, HealthCheck, HealthCheck, "health_checks"
                )
            except Exception as e:
                logger.warning(f"Health checks table migration skipped: {e}")
        else:
            logger.info("Health checks table not available, skipping")
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ Migration completed! Total records migrated: {total_migrated}")
        logger.info("=" * 60)
        
        logger.info("\n📝 Next steps:")
        logger.info("1. Update .env to use PostgreSQL:")
        logger.info("   DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname")
        logger.info("   OR set POSTGRES_* variables")
        logger.info("2. Test the bot with PostgreSQL")
        logger.info("3. Backup SQLite database (bot.db) before removing it")
        logger.info("4. Once verified, you can remove bot.db")
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        sqlite_session.close()
        postgres_session.close()
        sqlite_engine.dispose()
        postgres_engine.dispose()


if __name__ == "__main__":
    main()

