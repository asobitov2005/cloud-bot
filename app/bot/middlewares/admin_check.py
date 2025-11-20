from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from app.core.config import settings
from app.bot.translations import get_text
from app.models.crud import is_user_admin
from app.core.database import AsyncSession, get_db


class AdminCheckMiddleware(BaseMiddleware):
    """
    Middleware to check if user is admin
    Checks database for is_admin field or primary ADMIN_ID
    """
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        
        if not user:
            lang = data.get("lang", "uz")
            await event.answer(get_text("admin_only", lang))
            return
        
        # Get database session
        db: AsyncSession = data.get("db")
        if not db:
            # Fallback to primary admin ID if no database
            if user.id != settings.ADMIN_ID:
                lang = data.get("lang", "uz")
                await event.answer(get_text("admin_only", lang))
                return
        else:
            # Check if user is admin in database or primary admin
            is_admin = await is_user_admin(db, user.id, settings.ADMIN_ID)
            if not is_admin:
                lang = data.get("lang", "uz")
                await event.answer(get_text("admin_only", lang))
                return
        
        data["is_admin"] = True
        return await handler(event, data)

