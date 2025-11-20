from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class LanguageMiddleware(BaseMiddleware):
    """
    Middleware to attach user language to handler data
    """
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Get user from data (injected by UserCheckMiddleware)
        db_user = data.get("db_user")
        
        if db_user:
            data["lang"] = db_user.language
        else:
            data["lang"] = "uz"  # Default language
        
        return await handler(event, data)
