from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.models.crud import (
    get_users_count, get_files_count
)


router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message, lang: str, db: AsyncSession):
    """Show bot statistics"""
    # Get statistics
    users_count = await get_users_count(db)
    files_count = await get_files_count(db)
    
    # Send stats message
    stats_text = get_text(
        "stats_message",
        lang,
        users=users_count,
        files=files_count
    )
    
    await message.answer(stats_text, parse_mode="HTML")
