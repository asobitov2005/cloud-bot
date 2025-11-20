from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.models.crud import (
    get_users_count, get_files_count, get_total_downloads,
    get_top_downloaded_files
)


router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message, lang: str, db: AsyncSession):
    """Show bot statistics"""
    # Get statistics
    users_count = await get_users_count(db)
    files_count = await get_files_count(db)
    downloads_count = await get_total_downloads(db)
    top_files = await get_top_downloaded_files(db, limit=10)
    
    # Format top files
    top_files_text = ""
    for idx, item in enumerate(top_files, 1):
        file = item["file"]
        downloads = item["downloads"]
        top_files_text += f"{idx}. {file.title} - {downloads} downloads\n"
    
    if not top_files_text:
        top_files_text = "No downloads yet"
    
    # Send stats message
    stats_text = get_text(
        "stats_message",
        lang,
        users=users_count,
        files=files_count,
        downloads=downloads_count,
        top_files=top_files_text
    )
    
    await message.answer(stats_text, parse_mode="HTML")
