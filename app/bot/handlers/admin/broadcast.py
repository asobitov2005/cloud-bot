from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.models.crud import get_all_users
import asyncio


router = Router()


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, lang: str, db: AsyncSession):
    """Broadcast message to all users"""
    # Parse message from command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Usage: /broadcast <message>")
        return
    
    broadcast_text = parts[1]
    
    # Get all non-blocked users
    users = await get_all_users(db, skip=0, limit=10000)
    non_blocked_users = [u for u in users if not u.is_blocked]
    
    # Send message to all users
    sent_count = 0
    failed_count = 0
    
    status_msg = await message.answer(f"📤 Sending to {len(non_blocked_users)} users...")
    
    for user in non_blocked_users:
        try:
            await message.bot.send_message(
                chat_id=user.telegram_id,
                text=f"📢 <b>Broadcast Message</b>\n\n{broadcast_text}",
                parse_mode="HTML"
            )
            sent_count += 1
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.05)
        except Exception as e:
            failed_count += 1
            continue
    
    # Update status
    await status_msg.edit_text(
        get_text("broadcast_sent", lang, count=sent_count) + 
        f"\n❌ Failed: {failed_count}"
    )
