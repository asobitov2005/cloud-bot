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
                if isinstance(event, Message):
                    await event.answer(get_text("you_are_blocked", db_user.language))
                elif isinstance(event, CallbackQuery):
                    await event.answer(get_text("you_are_blocked", db_user.language), show_alert=True)
                return
            
            # Add user to data
            data["db_user"] = db_user
            data["db"] = db
        
            return await handler(event, data)
