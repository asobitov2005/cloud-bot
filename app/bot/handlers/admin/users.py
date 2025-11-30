from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.bot.keyboards.inline import get_user_actions_keyboard, get_pagination_keyboard
from app.models.crud import get_all_users, block_user, unblock_user
import math


router = Router()


@router.message(Command("users"))
async def cmd_users(message: Message, lang: str, db: AsyncSession):
    """Show users list"""
    # Get users
    users = await get_all_users(db, skip=0, limit=50)
    
    if not users:
        await message.answer("🚫 No users found")
        return
    
    # Send header
    await message.answer("👥 <b>Users List</b>", parse_mode="HTML")
    
    # Send each user (first 10)
    for user in users[:10]:
        user_text = f"""
👤 <b>{user.full_name or 'Unknown'}</b>
🆔 ID: {user.telegram_id}
👤 Username: @{user.username or 'N/A'}
🌐 Language: {user.language}
📅 Joined: {user.joined_at.strftime('%Y-%m-%d')}
{'🚫 <b>BLOCKED</b>' if user.is_blocked else '✅ Active'}
"""
        
        keyboard = get_user_actions_keyboard(user.id, user.is_blocked)
        await message.answer(user_text, reply_markup=keyboard, parse_mode="HTML")
    
    # Show pagination if more than 10
    if len(users) > 10:
        total_pages = math.ceil(len(users) / 10)
        pagination_kb = get_pagination_keyboard(0, total_pages, "users", lang)
        await message.answer(
            f"Page 1/{total_pages}",
            reply_markup=pagination_kb
        )


@router.callback_query(F.data.startswith("block_user:"))
async def handle_block_user(callback: CallbackQuery, lang: str, db: AsyncSession):
    """Block user"""
    user_id = int(callback.data.split(":")[1])
    
    await block_user(db, user_id)
    await callback.answer(get_text("user_blocked", lang), show_alert=True)
    
    # Update message
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_user_actions_keyboard(user_id, True)
        )
    except:
        pass


@router.callback_query(F.data.startswith("unblock_user:"))
async def handle_unblock_user(callback: CallbackQuery, lang: str, db: AsyncSession):
    """Unblock user"""
    user_id = int(callback.data.split(":")[1])
    
    await unblock_user(db, user_id)
    await callback.answer(get_text("user_unblocked", lang), show_alert=True)
    
    # Update message
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_user_actions_keyboard(user_id, False)
        )
    except:
        pass
