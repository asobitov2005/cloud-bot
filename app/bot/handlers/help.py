from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.core.config import settings


router = Router()


@router.message(Command("help"))
@router.message(F.text.in_([
    "❓ Yordam", "❓ Help", "❓ Помощь"
]))
async def show_help(message: Message, lang: str, db: AsyncSession):
    """Show help message"""
    # Get admin display username from settings
    from app.models.crud import get_setting
    
    admin_username = "admin"  # Default fallback
    try:
        # First try to get custom display username from settings
        display_username = await get_setting(db, "admin_display_username")
        if display_username:
            admin_username = display_username
        else:
            # Fallback to Telegram username
            from app.core.config import settings
            from app.models.crud import get_user_by_telegram_id
            from sqlalchemy import select
            from app.models.base import User
            
            # Try to get primary admin user
            admin_user = await get_user_by_telegram_id(db, settings.ADMIN_ID)
            if admin_user and admin_user.username:
                admin_username = admin_user.username
            else:
                # Try to get any admin user
                result = await db.execute(
                    select(User).where(User.is_admin == True).limit(1)
                )
                admin_user = result.scalar_one_or_none()
                if admin_user and admin_user.username:
                    admin_username = admin_user.username
    except Exception:
        pass  # Use default if can't get admin username
    
    help_text = get_text("help_message", lang, admin_username=admin_username)
    
    await message.answer(help_text, parse_mode="HTML")
