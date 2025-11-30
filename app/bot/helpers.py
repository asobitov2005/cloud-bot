"""
Helper functions for bot operations
"""
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
import logging

logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable format
    
    Args:
        size_bytes: File size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB", "500 KB")
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    # Format with appropriate decimal places
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    elif size < 10:
        return f"{size:.2f} {units[unit_index]}"
    elif size < 100:
        return f"{size:.1f} {units[unit_index]}"
    else:
        return f"{int(size)} {units[unit_index]}"


async def safe_answer_callback(callback: CallbackQuery, text: str = None, show_alert: bool = False) -> bool:
    """
    Safely answer a callback query, handling expired queries gracefully.
    
    Telegram callback queries expire after ~10 seconds. This function:
    - Answers immediately if possible
    - Catches and logs expired query errors without raising
    - Returns True if answered successfully, False if expired
    
    Args:
        callback: CallbackQuery instance
        text: Optional text to show in answer
        show_alert: Whether to show as alert
    
    Returns:
        True if answered successfully, False if query expired
    """
    try:
        if text:
            await callback.answer(text, show_alert=show_alert)
        else:
            await callback.answer()
        return True
    except TelegramBadRequest as e:
        # Check if it's the "query is too old" error
        error_message = str(e).lower()
        if "query is too old" in error_message or "query id is invalid" in error_message:
            logger.debug(
                f"Callback query expired for user {callback.from_user.id}, "
                f"query_id: {callback.id}. This is normal for slow operations."
            )
            return False
        else:
            # Re-raise other TelegramBadRequest errors
            raise
    except Exception as e:
        # Log other errors but don't raise (to prevent breaking the handler)
        logger.warning(f"Error answering callback query: {e}")
        return False
