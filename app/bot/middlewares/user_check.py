from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.crud import get_user_by_telegram_id, create_user


class UserCheckMiddleware(BaseMiddleware):
    """
    Middleware to check if user exists and create if not
    Also checks if user is blocked
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
        
        # Get database session
        async with AsyncSessionLocal() as db:
            # Check if user exists
            db_user = await get_user_by_telegram_id(db, user.id)
            
            if not db_user:
                # Create new user
                db_user = await create_user(
                    db,
                    telegram_id=user.id,
                    username=user.username,
                    full_name=user.full_name or user.first_name,
                    language="uz"  # Default language
                )
            
            # Check if user is blocked
            if db_user.is_blocked:
                from app.bot.translations import get_text
                from app.models.crud import get_setting
                
                # Get admin display username from settings
                admin_username = "admin"  # Default fallback
                try:
                    # First try to get custom display username from settings
                    display_username = await get_setting(db, "admin_display_username")
                    if display_username:
                        admin_username = display_username
                    else:
                        # Fallback to Telegram username
                        from app.core.config import settings
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
                
                blocked_text = get_text("you_are_blocked", db_user.language, admin_username=admin_username)
                if isinstance(event, Message):
                    await event.answer(blocked_text)
                elif isinstance(event, CallbackQuery):
                    await event.answer(blocked_text, show_alert=True)
                return
            
            # Add user to data
            data["db_user"] = db_user
            data["db"] = db
        
            return await handler(event, data)
