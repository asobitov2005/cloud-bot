from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from app.bot.translations import get_text
from app.bot.keyboards.reply import get_language_keyboard, get_main_menu_keyboard
from app.models.crud import update_user_language, get_force_subscribe_channels
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

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
    
    # Always show main menu on /start
    # If user wants to change language, they can use the button
    await message.answer(
        get_text("welcome", lang),
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML"
    )


@router.message(F.text.in_([
    "🌐 Tilni o'zgartirish", "🌐 Change Language", "🌐 Изменить язык"
]))
async def cmd_change_language(message: Message):
    """Handle change language button"""
    # We don't know the language here easily without db_user, but we can default to uz or try to get it
    # Actually, we can get lang from middleware if we add it to arguments
    # But for now let's just show it in English or multi-language?
    # The buttons are multi-language anyway.
    # Let's just use a generic message or "uz" default.
    await message.answer(
        get_text("select_language", "uz"), 
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


@router.callback_query(F.data == "fsub_confirm")
async def handle_fsub_confirm(callback: CallbackQuery, lang: str, db: AsyncSession, db_user):
    """Handle confirmation that user has joined channels"""
    # Get force subscribe channels
    channels = await get_force_subscribe_channels(db)
    
    if not channels:
        await callback.answer(get_text("fsub_no_channels", lang), show_alert=True)
        return
    
    # Check if user is member of all channels
    bot = callback.bot
    user = callback.from_user
    missing_channels = []
    cannot_verify_count = 0
    
    for channel in channels:
        channel_id = channel.get("channel_id")
        channel_username = channel.get("channel_username", "")
        channel_title = channel.get("channel_title", "")
        
        try:
            # Check if user is member of the channel
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user.id)
            
            # Valid member statuses: "member", "administrator", "creator", "restricted"
            # Invalid statuses: "left", "kicked"
            from aiogram.enums import ChatMemberStatus
            member_status = member.status
            
            if member_status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                # User is not a member
                if channel_username:
                    missing_channels.append(f"@{channel_username}")
                elif channel_title:
                    missing_channels.append(channel_title)
                else:
                    missing_channels.append(f"Channel {channel_id}")
            # If user is a member (status is member, administrator, creator, restricted), continue
                    
        except TelegramForbiddenError:
            # Bot doesn't have access - cannot verify
            logger.warning(f"Bot cannot check membership for channel {channel_id} - bot needs admin rights. Cannot verify, but allowing access.")
            cannot_verify_count += 1
            continue
        except TelegramBadRequest as e:
            error_msg = str(e).lower()
            if "member list is inaccessible" in error_msg:
                # Can't access member list - cannot verify
                logger.warning(f"Cannot access member list for channel {channel_id} - bot needs admin rights. Cannot verify, but allowing access.")
                cannot_verify_count += 1
                continue
            elif "chat not found" in error_msg or "user not found" in error_msg:
                logger.error(f"Channel {channel_id} not found: {e}")
                # If channel doesn't exist, block access
                if channel_username:
                    missing_channels.append(f"@{channel_username} (Not found)")
                elif channel_title:
                    missing_channels.append(f"{channel_title} (Not found)")
                else:
                    missing_channels.append(f"Channel {channel_id} (Not found)")
                continue
            else:
                logger.warning(f"Error checking channel {channel_id}: {e} - cannot verify, but allowing access.")
                cannot_verify_count += 1
                continue
        except Exception as e:
            logger.warning(f"Unexpected error checking channel {channel_id}: {e} - cannot verify, but allowing access.")
            cannot_verify_count += 1
            continue
    
    # If user is missing any channels that we CAN verify, block access
    if missing_channels:
        channels_text = "\n".join([f"• {ch}" for ch in missing_channels])
        # Get translation and strip HTML tags for alert (alerts don't support HTML)
        import re
        alert_text = get_text("fsub_not_joined", lang, channels=channels_text)
        # Strip HTML tags for alert
        alert_text = re.sub(r'<[^>]+>', '', alert_text)
        await callback.answer(
            alert_text,
            show_alert=True
        )
        return
    
    # If we couldn't verify some channels, block access and tell user bot needs admin rights
    if cannot_verify_count > 0:
        logger.warning(f"User {user.id} clicked confirm but bot cannot verify {cannot_verify_count} channels - bot needs admin rights")
        await callback.answer(
            "❌ Bot cannot verify your membership. Please make sure the bot is an admin in the channel with permission to view members.",
            show_alert=True
        )
        return
    
    # Success - user joined all channels and we verified membership
    await callback.answer(get_text("fsub_joined_success", lang), show_alert=True)
    
    # Delete the fsub message
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    # Send welcome message
    await callback.message.answer(
        get_text("welcome", lang),
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode="HTML"
    )
