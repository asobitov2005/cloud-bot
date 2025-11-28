"""Helper functions for bot operations"""
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.crud import get_setting


async def get_thumbnail_for_file(bot: Bot, file_id: str, current_thumbnail: str, db: AsyncSession) -> str:
    """
    Get thumbnail for a file. Returns current thumbnail if exists, 
    otherwise returns default thumbnail if file is ≤20MB.
    
    Args:
        bot: Bot instance
        file_id: Telegram file_id of the file
        current_thumbnail: Current thumbnail_id from database
        db: Database session
        
    Returns:
        Thumbnail file_id or None
    """
    # If file already has a thumbnail, use it
    if current_thumbnail:
        return current_thumbnail
    
    # Get default thumbnail from settings
    default_thumbnail = await get_setting(db, "default_thumbnail_id")
    if not default_thumbnail:
        return None
    
    # Check file size
    try:
        file_info = await bot.get_file(file_id)
        file_size_mb = file_info.file_size / (1024 * 1024) if file_info.file_size else 0
        
        # Only apply default thumbnail if file is 20MB or less
        if file_size_mb <= 20:
            return default_thumbnail
    except Exception:
        # If we can't get file info, don't apply default thumbnail
        pass
    
    return None
