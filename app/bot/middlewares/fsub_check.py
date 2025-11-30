from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.crud import get_force_subscribe_channels
from app.bot.translations import get_text
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Store user confirmations when we can't verify (user_id -> confirmation_time)
# This allows access for 1 hour after confirmation when bot can't verify
_user_fsub_confirmations: Dict[int, datetime] = {}


class FSubCheckMiddleware(BaseMiddleware):
    """
    Middleware to check if user is member of required channels
    Blocks access to bot until user joins all required channels
    Checks on EVERY request from the user
    """
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Get user from event
        user = event.from_user
        if not user:
            return await handler(event, data)
        
        # Get bot from data (set by dispatcher)
        bot = data.get('bot')
        if not bot:
            # Fallback: try to get from event
            bot = getattr(event, 'bot', None)
        if not bot:
            return await handler(event, data)
        
        # Get database session
        async with AsyncSessionLocal() as db:
            # Check if user is admin - admins bypass fsub check
            db_user = data.get("db_user")
            if db_user and db_user.is_admin:
                return await handler(event, data)
            
            # Get force subscribe channels
            channels = await get_force_subscribe_channels(db)
            
            # If no channels required, allow access
            if not channels:
                return await handler(event, data)
            
            # Allow fsub_confirm callback to pass through (handler will check membership)
            # This is the only exception - user needs to be able to confirm they joined
            if isinstance(event, CallbackQuery) and event.data == "fsub_confirm":
                return await handler(event, data)
            
            # Check membership for all required channels on EVERY request
            user_id = user.id  # Define user_id before loop (used in exception handlers)
            missing_channels = []
            missing_channel_ids = set()  # Track channel IDs that user hasn't joined
            cannot_verify_channels = []  # Channels we can't verify but still need to show
            verified_member_channels = []  # Channels we successfully verified user is a member
            
            logger.debug(f"FSub check for user {user_id}: checking {len(channels)} channels")
            
            for channel in channels:
                channel_id = channel.get("channel_id")
                channel_username = channel.get("channel_username", "")
                channel_title = channel.get("channel_title", "")
                
                # Format channel name for display
                if channel_username:
                    channel_display = f"@{channel_username}"
                elif channel_title:
                    channel_display = channel_title
                else:
                    channel_display = f"Channel {channel_id}"
                
                try:
                    # Check if user is member of the channel
                    member = await bot.get_chat_member(chat_id=channel_id, user_id=user.id)
                    
                    # Valid member statuses: "member", "administrator", "creator", "restricted"
                    # Invalid statuses: "left", "kicked"
                    # member.status is a ChatMemberStatus enum, get the value
                    from aiogram.enums import ChatMemberStatus
                    member_status = member.status
                    
                    if member_status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                        # User is not a member
                        missing_channels.append(channel_display)
                        missing_channel_ids.add(channel_id)
                        # Clear confirmation cache since we verified user is NOT a member
                        if user_id in _user_fsub_confirmations:
                            del _user_fsub_confirmations[user_id]
                            logger.info(f"Cleared fsub confirmation cache for user {user_id} - verified they left channel {channel_id}")
                    else:
                        # User is a member - verified successfully (member, administrator, creator, restricted)
                        verified_member_channels.append(channel_display)
                        # Clear confirmation cache since we successfully verified
                        if user_id in _user_fsub_confirmations:
                            del _user_fsub_confirmations[user_id]
                            logger.info(f"Cleared fsub confirmation cache for user {user_id} - verified membership in channel {channel_id}")
                    
                except TelegramBadRequest as e:
                    # Channel not found or other error
                    error_msg = str(e).lower()
                    if "chat not found" in error_msg or "user not found" in error_msg:
                        logger.error(f"Channel {channel_id} not found or user {user.id} not accessible: {e}")
                        # Block access if channel doesn't exist
                        missing_channels.append(f"{channel_display} (Not found)")
                        missing_channel_ids.add(channel_id)
                    elif "member list is inaccessible" in error_msg:
                        # Bot can't access member list - this means bot is NOT admin or doesn't have rights
                        # We MUST block access - bot needs to be admin to enforce fsub
                        logger.error(f"Cannot access member list for channel {channel_id} - bot MUST be admin in the channel to enforce fsub! Blocking access.")
                        missing_channels.append(f"{channel_display} (Bot needs admin rights)")
                        missing_channel_ids.add(channel_id)
                    else:
                        logger.warning(f"Bad request checking channel {channel_id}: {e} - blocking access")
                        missing_channels.append(f"{channel_display} (Error)")
                        missing_channel_ids.add(channel_id)
                except TelegramForbiddenError:
                    # Bot doesn't have access to check membership - bot is NOT admin
                    # We MUST block access - bot needs to be admin to enforce fsub
                    logger.error(f"Bot cannot check membership for channel {channel_id} - bot MUST be admin in the channel to enforce fsub! Blocking access.")
                    missing_channels.append(f"{channel_display} (Bot needs admin rights)")
                    missing_channel_ids.add(channel_id)
                except Exception as e:
                    logger.error(f"Unexpected error checking channel {channel_id}: {e} - blocking access")
                    # Block access on unexpected errors - bot needs to be able to verify
                    missing_channels.append(f"{channel_display} (Error)")
                    missing_channel_ids.add(channel_id)
            
            # If user is missing verified channels, always block
            # This takes priority - if we verified they left, block them
            logger.debug(f"FSub check result for user {user_id}: missing={len(missing_channels)}, verified={len(verified_member_channels)}")
            if missing_channels:
                # User is definitely not a member - show fsub message
                # Clear any confirmation cache since we verified they're not a member
                if user_id in _user_fsub_confirmations:
                    del _user_fsub_confirmations[user_id]
                    logger.info(f"Cleared fsub confirmation cache for user {user_id} - verified they are not a member")
                
                # Filter channels to only include the ones user hasn't joined
                missing_channels_list = [ch for ch in channels if ch.get("channel_id") in missing_channel_ids]
                
                # Show fsub message with only missing channels
                channels_text = "\n".join([f"• {ch}" for ch in missing_channels])
                
                # Get user language
                lang = data.get("lang", "uz")
                
                # Get keyboard with only missing channel buttons and confirmation
                from app.bot.keyboards.inline import get_fsub_channels_keyboard
                keyboard = get_fsub_channels_keyboard(missing_channels_list, lang)
                
                # Send message asking to join channels with inline buttons
                if isinstance(event, Message):
                    await event.answer(
                        get_text("fsub_join_required", lang, channels=channels_text),
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                        reply_markup=keyboard
                    )
                elif isinstance(event, CallbackQuery):
                    # For callback queries, edit the message or answer
                    try:
                        await event.message.edit_text(
                            get_text("fsub_join_required", lang, channels=channels_text),
                            parse_mode="HTML",
                            disable_web_page_preview=True,
                            reply_markup=keyboard
                        )
                        await event.answer()
                    except Exception:
                        # If edit fails, just answer
                        await event.answer(
                            get_text("fsub_join_required", lang, channels=channels_text),
                            show_alert=True
                        )
                
                return  # Block handler execution
            
            # All channels verified and user is member - allow access
            else:
                # All channels verified and user is member - allow access
                # Clear confirmation cache since we successfully verified
                if user_id in _user_fsub_confirmations:
                    del _user_fsub_confirmations[user_id]
                    logger.info(f"Cleared fsub confirmation cache for user {user_id} - all channels verified")
                return await handler(event, data)

