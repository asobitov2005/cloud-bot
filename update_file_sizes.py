#!/usr/bin/env python3
"""
Update file sizes for existing files in database

This script fetches file size from Telegram API for all files that don't have size stored,
and updates the database.

Usage:
    python update_file_sizes.py
"""
import asyncio
import logging
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.base import File
from app.bot.main import _bot_instance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_file_sizes():
    """Update file sizes for all files without size"""
    async with AsyncSessionLocal() as db:
        # Get all files without size
        query = select(File).where(File.file_size == None)
        result = await db.execute(query)
        files = result.scalars().all()
        
        if not files:
            logger.info("✅ All files already have size information!")
            return
        
        logger.info(f"📊 Found {len(files)} files without size. Updating...")
        
        updated_count = 0
        failed_count = 0
        
        for idx, file in enumerate(files, 1):
            try:
                # Get file info from Telegram
                file_info = await _bot_instance.get_file(file.file_id)
                
                if file_info and file_info.file_size:
                    file.file_size = file_info.file_size
                    updated_count += 1
                    logger.info(f"✅ [{idx}/{len(files)}] Updated {file.title}: {file_info.file_size} bytes")
                else:
                    logger.warning(f"⚠️  [{idx}/{len(files)}] No size info for: {file.title}")
                    failed_count += 1
                
                # Commit every 10 files to avoid losing progress
                if idx % 10 == 0:
                    await db.commit()
                    logger.info(f"💾 Committed batch {idx//10}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ [{idx}/{len(files)}] Error for {file.title}: {e}")
                failed_count += 1
        
        # Final commit
        await db.commit()
        
        logger.info("=" * 60)
        logger.info(f"✅ Updated: {updated_count} files")
        logger.info(f"❌ Failed: {failed_count} files")
        logger.info(f"📊 Total processed: {len(files)} files")
        logger.info("=" * 60)


async def main():
    """Main function"""
    logger.info("🚀 Starting file size update...")
    logger.info("=" * 60)
    
    # Wait for bot to initialize
    await asyncio.sleep(2)
    
    if not _bot_instance:
        logger.error("❌ Bot instance not available! Make sure the bot is running.")
        return
    
    await update_file_sizes()
    logger.info("✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
