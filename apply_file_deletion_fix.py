"""
Apply database migration to fix file deletion
This updates the foreign key constraint to allow file deletion while preserving downloads
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, get_database_url
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def apply_migration():
    """Apply the foreign key constraint change"""
    db_url = get_database_url()
    if not db_url.startswith("postgresql"):
        logger.error("This migration is only for PostgreSQL!")
        return False
    
    try:
        async with AsyncSessionLocal() as session:
            logger.info("Applying file deletion fix...")
            
            # Drop existing constraint
            try:
                await session.execute(text(
                    "ALTER TABLE downloads DROP CONSTRAINT IF EXISTS downloads_file_id_fkey"
                ))
                logger.info("Dropped existing constraint")
            except Exception as e:
                logger.warning(f"Could not drop constraint (might not exist): {e}")
            
            # Add new constraint with SET NULL
            await session.execute(text(
                """ALTER TABLE downloads 
                ADD CONSTRAINT downloads_file_id_fkey 
                FOREIGN KEY (file_id) 
                REFERENCES files(id) 
                ON DELETE SET NULL"""
            ))
            await session.commit()
            
            logger.info("✅ Migration applied successfully!")
            logger.info("Files can now be deleted while preserving download records")
            return True
            
    except Exception as e:
        logger.error(f"Error applying migration: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    asyncio.run(apply_migration())

