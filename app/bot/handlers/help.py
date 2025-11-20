from aiogram import Router, F
from aiogram.types import Message
from app.bot.translations import get_text
from app.core.config import settings


router = Router()


@router.message(F.text.in_([
    "❓ Yordam", "❓ Help", "❓ Помощь"
]))
async def show_help(message: Message, lang: str):
    """Show help message"""
    # Get admin username from settings or use default
    admin_username = "admin"  # You can configure this in settings
    
    help_text = get_text("help_message", lang, admin_username=admin_username)
    
    await message.answer(help_text, parse_mode="HTML")
