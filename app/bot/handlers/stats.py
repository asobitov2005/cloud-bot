from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.models.crud import (
    get_users_count, get_files_count, get_total_downloads, get_total_files_volume
)
from app.bot.helpers import format_file_size


router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message, lang: str, db: AsyncSession):
    """Show bot statistics for all users"""
    # Get statistics
    users_count = await get_users_count(db)
    files_count = await get_files_count(db)
    downloads_count = await get_total_downloads(db)
    files_volume = await get_total_files_volume(db)
    
    # Format storage
    storage_formatted = files_volume.get("formatted", "0 B")
    
    # Send stats message
    stats_text = get_text(
        "stats_message",
        lang,
        users=users_count,
        files=files_count,
        storage=storage_formatted,
        downloads=downloads_count
    )
    
    await message.answer(stats_text, parse_mode="HTML")

