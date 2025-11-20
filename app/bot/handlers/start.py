from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.bot.translations import get_text
from app.bot.keyboards.reply import get_language_keyboard, get_main_menu_keyboard
from app.models.crud import update_user_language
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db_user, lang: str, db: AsyncSession):
    """Handle /start command"""
    # Set commands for this user based on their admin status
    from app.bot.main import update_user_commands
    from app.core.config import settings
    from app.models.crud import is_user_admin
    
    try:
        # Check if user is admin
        user_is_admin = await is_user_admin(db, message.from_user.id, settings.ADMIN_ID)
        # Update commands for this user
        await update_user_commands(message.from_user.id, user_is_admin)
    except Exception as e:
        # Log error but continue
        import logging
        logging.getLogger(__name__).warning(f"Failed to update commands: {e}")
    
    # If user already has language, show main menu
    if db_user.language and db_user.language != "uz":
        await message.answer(
            get_text("welcome", lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        # Show language selection
        await message.answer(
            get_text("welcome", "uz"),
            reply_markup=get_language_keyboard()
        )


@router.message(F.text.in_(["🇺🇿 O'zbekcha", "🇬🇧 English", "🇷🇺 Русский"]))
async def select_language(message: Message, db_user, db: AsyncSession):
    """Handle language selection"""
    # Map button text to language code
    lang_map = {
        "🇺🇿 O'zbekcha": "uz",
        "🇬🇧 English": "en",
        "🇷🇺 Русский": "ru"
    }
    
    selected_lang = lang_map.get(message.text, "uz")
    
    # Update user language
    await update_user_language(db, db_user.id, selected_lang)
    
    # Show confirmation and main menu
    await message.answer(
        get_text("language_selected", selected_lang),
        reply_markup=get_main_menu_keyboard(selected_lang)
    )
