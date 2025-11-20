from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.bot.translations import get_text
from typing import List


def get_file_actions_keyboard(file_id: int, lang: str = "uz", 
                              show_remove: bool = False) -> InlineKeyboardMarkup:
    """
    Get inline keyboard for file actions
    
    Args:
        file_id: File ID
        lang: User language
        show_remove: Show remove button instead of save
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=get_text("btn_download", lang),
        callback_data=f"download:{file_id}"
    )
    
    if show_remove:
        builder.button(
            text=get_text("btn_remove", lang),
            callback_data=f"remove:{file_id}"
        )
    else:
        builder.button(
            text=get_text("btn_save", lang),
            callback_data=f"save:{file_id}"
        )
    
    builder.adjust(2)
    return builder.as_markup()


def get_pagination_keyboard(current_page: int, total_pages: int, 
                           prefix: str, lang: str = "uz") -> InlineKeyboardMarkup:
    """
    Get numbered pagination keyboard (1 2 3 4 5)
    
    Args:
        current_page: Current page number (0-indexed)
        total_pages: Total number of pages
        prefix: Callback data prefix (e.g., "search", "downloads", "saved")
        lang: User language
    """
    builder = InlineKeyboardBuilder()
    
    # Calculate range of pages to show
    # We want to show up to 5 pages centered around current page
    start_page = max(0, current_page - 2)
    end_page = min(total_pages, start_page + 5)
    
    # Adjust start if we're near the end
    if end_page - start_page < 5:
        start_page = max(0, end_page - 5)
    
    buttons = []
    
    # Previous button (if not on first page)
    if current_page > 0:
        buttons.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=f"{prefix}_page:{current_page - 1}"
        ))
    
    # Numbered buttons
    for i in range(start_page, end_page):
        text = f"· {i + 1} ·" if i == current_page else str(i + 1)
        callback_data = "noop" if i == current_page else f"{prefix}_page:{i}"
        buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    # Next button (if not on last page)
    if current_page < total_pages - 1:
        buttons.append(InlineKeyboardButton(
            text="➡️",
            callback_data=f"{prefix}_page:{current_page + 1}"
        ))
    
    builder.row(*buttons)
    return builder.as_markup()


def get_user_actions_keyboard(user_id: int, is_blocked: bool) -> InlineKeyboardMarkup:
    """Get admin actions keyboard for user management"""
    builder = InlineKeyboardBuilder()
    
    if is_blocked:
        builder.button(
            text="✅ Unblock",
            callback_data=f"unblock_user:{user_id}"
        )
    else:
        builder.button(
            text="🚫 Block",
            callback_data=f"block_user:{user_id}"
        )
    
    builder.button(
        text="📊 View Stats",
        callback_data=f"user_stats:{user_id}"
    )
    
    builder.adjust(2)
    return builder.as_markup()


def get_file_list_keyboard(files: List[tuple], lang: str = "uz", 
                          current_page: int = 0, total_pages: int = 1,
                          prefix: str = "search") -> InlineKeyboardMarkup:
    """
    Get keyboard with file list and actions
    
    Args:
        files: List of (file_id, file_title) tuples
        lang: User language
        current_page: Current page number
        total_pages: Total pages
        prefix: Callback prefix
    """
    builder = InlineKeyboardBuilder()
    
    # Add file buttons with actions
    for file_id, _ in files:
        builder.row(
            InlineKeyboardButton(
                text=get_text("btn_download", lang),
                callback_data=f"download:{file_id}"
            ),
            InlineKeyboardButton(
                text=get_text("btn_save", lang),
                callback_data=f"save:{file_id}"
            )
        )
    
    # Add pagination if needed
    if total_pages > 1:
        pagination_buttons = []
        
        if current_page > 0:
            pagination_buttons.append(InlineKeyboardButton(
                text=get_text("btn_prev", lang),
                callback_data=f"{prefix}_page:{current_page - 1}"
            ))
        
        pagination_buttons.append(InlineKeyboardButton(
            text=get_text("page_info", lang, current=current_page + 1, total=total_pages),
            callback_data="page_info"
        ))
        
        if current_page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton(
                text=get_text("btn_next", lang),
                callback_data=f"{prefix}_page:{current_page + 1}"
            ))
        
        builder.row(*pagination_buttons)
    
    return builder.as_markup()
