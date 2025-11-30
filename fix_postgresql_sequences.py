"""
Fix PostgreSQL sequences after migration from SQLite

When migrating from SQLite to PostgreSQL, the auto-increment sequences
need to be reset to the maximum existing ID + 1 to prevent conflicts.
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import get_database_url, AsyncSessionLocal
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_sequence(table_name: str, id_column: str = "id"):
    """
    Fix the sequence for a table's primary key
    
    Args:
        table_name: Name of the table
        id_column: Name of the ID column (default: "id")
    """
    try:
        async with AsyncSessionLocal() as session:
            # Get the current maximum ID
            result = await session.execute(
                text(f"SELECT COALESCE(MAX({id_column}), 0) FROM {table_name}")
            )
            max_id = result.scalar() or 0
            
            # Get the sequence name (PostgreSQL convention: tablename_columnname_seq)
            sequence_name = f"{table_name}_{id_column}_seq"
            
            # Reset the sequence to max_id + 1
            await session.execute(
                text(f"SELECT setval('{sequence_name}', {max_id + 1}, false)")
            )
            await session.commit()
            
            logger.info(f"Fixed sequence for {table_name}: set to {max_id + 1}")
            return True
    except Exception as e:
        logger.error(f"Error fixing sequence for {table_name}: {e}")
        return False


async def fix_all_sequences():
    """Fix sequences for all tables with auto-increment IDs"""
    tables = [
        ("users", "id"),
        ("files", "id"),
        ("downloads", "id"),
        ("saved_list", "id"),
        ("settings", "id"),
        ("health_checks", "id"),
    ]
    
    logger.info("=" * 60)
    logger.info("Fixing PostgreSQL sequences after migration")
    logger.info("=" * 60)
    
    for table_name, id_column in tables:
        await fix_sequence(table_name, id_column)
    
    logger.info("=" * 60)
    logger.info("Sequence fix complete!")
    logger.info("=" * 60)


async def verify_sequences():
    """Verify that sequences are set correctly"""
    async with AsyncSessionLocal() as session:
        sequences = [
            ("users", "users_id_seq"),
            ("files", "files_id_seq"),
            ("downloads", "downloads_id_seq"),
            ("saved_list", "saved_list_id_seq"),
            ("settings", "settings_id_seq"),
            ("health_checks", "health_checks_id_seq"),
        ]
        
        logger.info("\nVerifying sequences:")
        for table_name, seq_name in sequences:
            try:
                # Get current sequence value
                result = await session.execute(
                    text(f"SELECT last_value FROM {seq_name}")
                )
                last_value = result.scalar()
                
                # Get max ID from table
                result = await session.execute(
                    text(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
                )
                max_id = result.scalar() or 0
                
                logger.info(
                    f"{table_name:20} - Sequence: {last_value:6}, "
                    f"Max ID: {max_id:6}, "
                    f"Next ID: {last_value + 1:6}"
                )
            except Exception as e:
                logger.warning(f"Could not verify {seq_name}: {e}")


if __name__ == "__main__":
    # Check if we're using PostgreSQL
    db_url = get_database_url()
    if not db_url.startswith("postgresql"):
        logger.error("This script is only for PostgreSQL databases!")
        exit(1)
    
    logger.info(f"Database URL: {db_url}")
    logger.info("")
    
    # Fix all sequences
    asyncio.run(fix_all_sequences())
    
    # Verify
    asyncio.run(verify_sequences())

