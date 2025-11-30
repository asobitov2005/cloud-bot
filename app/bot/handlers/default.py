from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.bot.translations import get_text
from app.bot.keyboards.reply import get_main_menu_keyboard
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.message(lambda msg: msg.text and not msg.text.startswith("/") and not msg.text.startswith("!"))
async def handle_unhandled_text(message: Message, lang: str, state: FSMContext):
    """
    Catch-all handler for unhandled text messages.
    Shows main menu options to the user.
    Excludes commands (messages starting with "/" or "!").
    """
    # Check if user is in any state - if so, don't interfere
    # State handlers should have higher priority, but this is a safety check
    current_state = await state.get_state()
    if current_state is not None:
        # User is in a state (like search, upload), let that handler deal with it
        # Don't process this message
        return
    
    # User sent random text - show menu options
    await message.answer(
        get_text("select_menu_option", lang),
        reply_markup=get_main_menu_keyboard(lang)
    )

