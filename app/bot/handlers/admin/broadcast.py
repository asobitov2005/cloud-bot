from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.models.crud import get_all_users
import asyncio
import logging
import html

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, lang: str, db: AsyncSession):
    """Broadcast message to all users"""
    # Parse message from command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("🚫 Usage: /broadcast <message>")
        return
    
    broadcast_text = parts[1]
    
    # Get all non-blocked users
    users = await get_all_users(db, skip=0, limit=10000)
    non_blocked_users = [u for u in users if not u.is_blocked]
    
    if not non_blocked_users:
        await message.answer("🚫 No users found to broadcast to.")
        return
    
    # Send message to all users
    sent_count = 0
    failed_count = 0
    blocked_count = 0
    not_found_count = 0
    
    status_msg = await message.answer(f"📤 Sending to {len(non_blocked_users)} users...")
    
    for user in non_blocked_users:
        try:
            # Escape HTML in user's broadcast text to prevent parsing errors
            safe_broadcast_text = html.escape(broadcast_text)
            await message.bot.send_message(
                chat_id=user.telegram_id,
                text=f"{safe_broadcast_text}",
                parse_mode="HTML"
            )
            sent_count += 1
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.05)
            
        except TelegramForbiddenError:
            # User blocked the bot
            blocked_count += 1
            failed_count += 1
            logger.debug(f"User {user.telegram_id} blocked the bot")
            
        except TelegramBadRequest as e:
            # Invalid chat ID or other bad request
            if "chat not found" in str(e).lower() or "chat_id" in str(e).lower():
                not_found_count += 1
                failed_count += 1
                logger.debug(f"Chat not found for user {user.telegram_id}: {e}")
            else:
                failed_count += 1
                logger.warning(f"Bad request for user {user.telegram_id}: {e}")
                
        except TelegramAPIError as e:
            # Other Telegram API errors
            failed_count += 1
            logger.warning(f"Telegram API error for user {user.telegram_id}: {e}")
            
        except Exception as e:
            # Unexpected errors
            failed_count += 1
            logger.error(f"Unexpected error sending to user {user.telegram_id}: {e}", exc_info=True)
    
    # Build status message
    status_text = get_text("broadcast_sent", lang, count=sent_count)
    if failed_count > 0:
        status_text += f"\n🚫 Failed: {failed_count}"
        if blocked_count > 0:
            status_text += f" (Blocked: {blocked_count})"
        if not_found_count > 0:
            status_text += f" (Not found: {not_found_count})"
    
    # Update status
    await status_msg.edit_text(status_text)
