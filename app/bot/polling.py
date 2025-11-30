"""
Optimized long polling configuration for aiogram 3.x
Includes automatic reconnection, error handling, and webhook fallback
"""
import asyncio
import logging
from typing import Optional
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError, TelegramServerError, TelegramAPIError
from aiogram.client.session.aiohttp import AiohttpSession
from app.core.config import settings

logger = logging.getLogger(__name__)


async def start_polling_optimized(
    bot: Bot,
    dp: Dispatcher,
    handle_signals: bool = False
) -> None:
    """
    Start polling with optimized configuration and automatic reconnection
    
    Features:
    - Optimized timeout settings to prevent network errors
    - Automatic reconnection with exponential backoff
    - Graceful error handling
    - Webhook fallback option
    
    Args:
        bot: Bot instance
        dp: Dispatcher instance
        handle_signals: Whether to handle system signals
    """
    reconnect_delay = settings.POLLING_RECONNECT_DELAY
    max_reconnect_delay = settings.POLLING_MAX_RECONNECT_DELAY
    backoff_multiplier = settings.POLLING_BACKOFF_MULTIPLIER
    
    while True:
        try:
            logger.info("Starting optimized long polling...")
            logger.info(f"Polling timeout: {settings.POLLING_TIMEOUT}s, "
                       f"Limit: {settings.POLLING_LIMIT}, "
                       f"API timeout: {settings.API_REQUEST_TIMEOUT}s")
            
            # Start polling with optimized settings
            await dp.start_polling(
                bot,
                polling_timeout=settings.POLLING_TIMEOUT,  # Wait up to 20s for updates
                limit=settings.POLLING_LIMIT,  # Get up to 100 updates per request
                allowed_updates=settings.POLLING_ALLOWED_UPDATES or dp.resolve_used_update_types(),
                close_timeout=settings.POLLING_CLOSE_TIMEOUT,
                handle_signals=handle_signals,
                # Additional parameters for stability
                drop_pending_updates=False,  # Don't drop updates on restart
                fast=True,  # Use fast polling (recommended for aiogram 3.x)
            )
            
            # If polling exits normally (not due to error), break
            logger.info("Polling stopped normally")
            break
            
        except TelegramNetworkError as e:
            # Network errors - retry with exponential backoff
            logger.warning(
                f"Network error during polling: {e}. "
                f"Reconnecting in {reconnect_delay:.1f}s..."
            )
            await asyncio.sleep(reconnect_delay)
            
            # Exponential backoff with max limit
            reconnect_delay = min(
                reconnect_delay * backoff_multiplier,
                max_reconnect_delay
            )
            
        except TelegramServerError as e:
            # Telegram server errors - retry with shorter delay
            logger.warning(
                f"Telegram server error: {e}. "
                f"Reconnecting in {reconnect_delay:.1f}s..."
            )
            await asyncio.sleep(reconnect_delay)
            
            # Reset delay for server errors (they're usually temporary)
            reconnect_delay = settings.POLLING_RECONNECT_DELAY
            
        except asyncio.CancelledError:
            logger.info("Polling cancelled, stopping...")
            await dp.stop_polling()
            raise
            
        except Exception as e:
            # Unexpected errors - log and retry
            logger.error(
                f"Unexpected error during polling: {e}",
                exc_info=True
            )
            logger.warning(f"Reconnecting in {reconnect_delay:.1f}s...")
            await asyncio.sleep(reconnect_delay)
            
            # Exponential backoff
            reconnect_delay = min(
                reconnect_delay * backoff_multiplier,
                max_reconnect_delay
            )


async def setup_webhook_fallback(
    bot: Bot,
    webhook_url: str,
    webhook_path: str = "/webhook"
) -> bool:
    """
    Setup webhook as fallback if polling fails repeatedly
    
    Args:
        bot: Bot instance
        webhook_url: Full webhook URL (e.g., https://example.com)
        webhook_path: Webhook path (default: /webhook)
    
    Returns:
        True if webhook setup successful, False otherwise
    """
    try:
        from app.bot.webhook import setup_webhook
        return await setup_webhook(bot, webhook_url, webhook_path)
    except Exception as e:
        logger.error(f"Error setting up webhook fallback: {e}", exc_info=True)
        return False


def create_optimized_bot_session() -> AiohttpSession:
    """
    Create optimized aiohttp session for Bot API requests
    
    Returns:
        Configured AiohttpSession with optimal timeout and connection settings
    
    Note: In aiogram 3.x, AiohttpSession expects a numeric timeout (float/int) in seconds,
    not a ClientTimeout object. The timeout represents the total request timeout.
    """
    # In aiogram 3.x, AiohttpSession expects a numeric timeout value (seconds)
    # This is the total timeout for API requests
    # The session will create its own ClientTimeout internally with this value
    timeout_seconds = float(settings.API_REQUEST_TIMEOUT)
    
    # Create AiohttpSession with optimized timeout
    # The timeout is used by aiogram internally to create ClientTimeout
    return AiohttpSession(
        timeout=timeout_seconds
    )

