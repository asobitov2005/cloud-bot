"""
Webhook support for aiogram 3.x
Alternative to long polling for production environments
"""
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Request, HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
_dp: Dispatcher = None
_bot: Bot = None


def set_dispatcher(dp: Dispatcher):
    """Set dispatcher for webhook handling"""
    global _dp
    _dp = dp


def set_bot(bot: Bot):
    """Set bot instance for webhook handling"""
    global _bot
    _bot = bot


@router.post("/webhook")
async def webhook_handler(request: Request):
    """
    Handle webhook updates from Telegram
    
    This endpoint receives updates from Telegram when webhook mode is enabled.
    """
    if not _dp:
        raise HTTPException(status_code=500, detail="Dispatcher not initialized")
    if not _bot:
        raise HTTPException(status_code=500, detail="Bot not initialized")
    
    try:
        # Parse update from request
        update_data = await request.json()
        update = Update(**update_data)
        
        # Process update through dispatcher
        await _dp.feed_update(_bot, update)
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def setup_webhook(bot: Bot, webhook_url: str, webhook_path: str = "/webhook") -> bool:
    """
    Setup webhook for receiving updates
    
    Args:
        bot: Bot instance
        webhook_url: Full webhook URL (e.g., https://example.com)
        webhook_path: Webhook path (default: /webhook)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        full_url = f"{webhook_url.rstrip('/')}{webhook_path}"
        logger.info(f"Setting up webhook: {full_url}")
        
        await bot.set_webhook(
            url=full_url,
            allowed_updates=None,  # All updates
            drop_pending_updates=False,
            secret_token=None  # Optional: add for security
        )
        
        # Verify webhook
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url == full_url:
            logger.info(f"Webhook set successfully: {webhook_info.url}")
            logger.info(f"Pending updates: {webhook_info.pending_update_count}")
            return True
        else:
            logger.warning(f"Webhook verification failed. Expected: {full_url}, Got: {webhook_info.url}")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}", exc_info=True)
        return False


async def remove_webhook(bot: Bot) -> bool:
    """Remove webhook and return to polling"""
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Webhook removed successfully")
        return True
    except Exception as e:
        logger.error(f"Error removing webhook: {e}", exc_info=True)
        return False

