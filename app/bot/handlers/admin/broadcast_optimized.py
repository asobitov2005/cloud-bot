"""Optimized broadcast handler with parallel processing and rate limiting"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.models.crud import get_all_users
from app.core.config import settings
from app.utils.retry import retry_async, with_timeout
import asyncio
import logging
import html

logger = logging.getLogger(__name__)

router = Router()


async def send_message_with_retry(bot, chat_id: int, text: str, max_retries: int = 3):
    """Send message with retry logic"""
    @with_timeout(settings.REQUEST_TIMEOUT)
    async def _send():
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    
    return await retry_async(
        _send,
        max_retries=max_retries,
        backoff_base=settings.RETRY_BACKOFF_BASE,
        exceptions=(TelegramAPIError, TelegramBadRequest)
    )


async def send_batch(bot, users: list, broadcast_text: str, batch_num: int):
    """Send messages to a batch of users in parallel"""
    tasks = []
    results = {"sent": 0, "failed": 0, "blocked": 0, "not_found": 0}
    
    for user in users:
        if user.is_blocked:
            continue
        
        task = send_message_with_retry(
            bot,
            user.telegram_id,
            broadcast_text,
            max_retries=settings.MAX_RETRIES
        )
        tasks.append((task, user))
    
    # Execute batch in parallel
    for task, user in tasks:
        try:
            await task
            results["sent"] += 1
        except TelegramForbiddenError:
            results["blocked"] += 1
            results["failed"] += 1
            logger.debug(f"User {user.telegram_id} blocked the bot")
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower() or "chat_id" in str(e).lower():
                results["not_found"] += 1
                results["failed"] += 1
            else:
                results["failed"] += 1
                logger.warning(f"Bad request for user {user.telegram_id}: {e}")
        except TelegramAPIError as e:
            results["failed"] += 1
            logger.warning(f"Telegram API error for user {user.telegram_id}: {e}")
        except Exception as e:
            results["failed"] += 1
            logger.error(f"Unexpected error sending to user {user.telegram_id}: {e}", exc_info=True)
    
    logger.info(f"Batch {batch_num} completed: {results['sent']} sent, {results['failed']} failed")
    return results


@router.message(Command("broadcast"))
async def cmd_broadcast_optimized(message: Message, lang: str, db: AsyncSession):
    """Optimized broadcast with parallel processing and rate limiting"""
    # Parse message from command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("🚫 Usage: /broadcast <message>")
        return
    
    broadcast_text = parts[1]
    
    # Escape HTML to prevent parsing errors
    safe_broadcast_text = html.escape(broadcast_text)
    
    # Get all non-blocked users
    users = await get_all_users(db, skip=0, limit=10000)
    non_blocked_users = [u for u in users if not u.is_blocked]
    
    if not non_blocked_users:
        await message.answer("🚫 No users found to broadcast to.")
        return
    
    total_users = len(non_blocked_users)
    batch_size = settings.BROADCAST_BATCH_SIZE
    
    # Send initial status
    status_msg = await message.answer(
        f"📤 Sending to {total_users} users in batches of {batch_size}...\n"
        f"⏳ Processing batch 1/{((total_users - 1) // batch_size) + 1}..."
    )
    
    # Process in batches
    total_results = {"sent": 0, "failed": 0, "blocked": 0, "not_found": 0}
    batch_num = 0
    
    for i in range(0, total_users, batch_size):
        batch_num += 1
        batch = non_blocked_users[i:i + batch_size]
        total_batches = ((total_users - 1) // batch_size) + 1
        
        # Update status
        try:
            await status_msg.edit_text(
                f"📤 Sending to {total_users} users...\n"
                f"⏳ Processing batch {batch_num}/{total_batches}...\n"
                f"✅ Sent: {total_results['sent']}, ❌ Failed: {total_results['failed']}"
            )
        except Exception:
            pass  # Ignore edit errors
        
        # Send batch in parallel
        batch_results = await send_batch(message.bot, batch, safe_broadcast_text, batch_num)
        
        # Accumulate results
        for key in total_results:
            total_results[key] += batch_results[key]
        
        # Rate limiting: wait between batches (except last batch)
        if i + batch_size < total_users:
            await asyncio.sleep(settings.BROADCAST_DELAY)
    
    # Build final status message
    status_text = get_text("broadcast_sent", lang, count=total_results["sent"])
    if total_results["failed"] > 0:
        status_text += f"\n🚫 Failed: {total_results['failed']}"
        if total_results["blocked"] > 0:
            status_text += f" (Blocked: {total_results['blocked']})"
        if total_results["not_found"] > 0:
            status_text += f" (Not found: {total_results['not_found']})"
    
    # Update final status
    await status_msg.edit_text(status_text)

