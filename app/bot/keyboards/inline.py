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
            text="▶️",
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
    
    # Add pagination if needed - all three buttons in one row
    if total_pages > 1:
        pagination_buttons = []
        
        # Previous button (left side)
        if current_page > 0:
            pagination_buttons.append(InlineKeyboardButton(
                text=get_text("btn_prev", lang),
                callback_data=f"{prefix}_page:{current_page - 1}"
            ))
        else:
            # Add empty button to maintain layout
            pagination_buttons.append(InlineKeyboardButton(
                text=" ",
                callback_data="noop"
            ))
        
        # Page info button (center)
        pagination_buttons.append(InlineKeyboardButton(
            text=get_text("page_info", lang, current=current_page + 1, total=total_pages),
            callback_data="page_info"
        ))
        
        # Next button (right side)
        if current_page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton(
                text=get_text("btn_next", lang),
                callback_data=f"{prefix}_page:{current_page + 1}"
            ))
        else:
            # Add empty button to maintain layout
            pagination_buttons.append(InlineKeyboardButton(
                text=" ",
                callback_data="noop"
            ))
        
        # Add all three buttons in a single row - Previous (left), Page Info (center), Next (right)
        builder.row(*pagination_buttons)
    
    return builder.as_markup()


def get_remove_fsub_keyboard(channels: List[dict], lang: str = "uz") -> InlineKeyboardMarkup:
    """
    Get inline keyboard for removing force subscribe channels
    
    Args:
        channels: List of channel dictionaries with channel_id, channel_username, channel_title
        lang: User language
    """
    builder = InlineKeyboardBuilder()
    
    for channel in channels:
        channel_id = channel.get("channel_id")
        channel_username = channel.get("channel_username", "")
        channel_title = channel.get("channel_title", "")
        
        # Format button text
        if channel_username:
            display = f"@{channel_username}"
        elif channel_title:
            display = channel_title[:30]  # Limit length
        else:
            display = f"Channel {channel_id}"
        
        builder.button(
            text=f"{get_text('btn_remove', lang)} {display}",
            callback_data=f"remove_fsub:{channel_id}"
        )
    
    builder.adjust(1)
    return builder.as_markup()


def get_fsub_channels_keyboard(channels: List[dict], lang: str = "uz") -> InlineKeyboardMarkup:
    """
    Get inline keyboard with channel buttons and confirmation button
    
    Args:
        channels: List of channel dictionaries with channel_id, channel_username, channel_title
        lang: User language
    """
    builder = InlineKeyboardBuilder()
    
    # Add channel buttons (URL buttons that open channels)
    for channel in channels:
        channel_id = channel.get("channel_id")
        channel_username = channel.get("channel_username", "")
        channel_title = channel.get("channel_title", "")
        invite_link = channel.get("invite_link", "")  # Support invite links
        
        # Format button text
        display = f"📢 {channel_title or (f'@{channel_username}' if channel_username else f'Channel {channel_id}')}"
        
        # Determine URL to use
        if invite_link:
            # Use invite link if available (tracks joins through this link)
            url = invite_link
        elif channel_username:
            # Use username link
            url = f"https://t.me/{channel_username}"
        else:
            # Use channel ID deep link
            channel_id_str = str(channel_id).replace("-100", "")
            url = f"https://t.me/c/{channel_id_str}/1"
        
        builder.button(
            text=display,
            url=url
        )
    
    # Add confirmation button below channels
    builder.button(
        text=get_text("btn_confirm_joined", lang),
        callback_data="fsub_confirm"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_search_results_keyboard(files: List, current_page: int = 0, 
                                total_pages: int = 1, lang: str = "uz",
                                file_sizes: dict = None) -> InlineKeyboardMarkup:
    """
    Get inline keyboard with search results as buttons
    
    Args:
        files: List of File objects
        current_page: Current page number
        total_pages: Total pages
        lang: User language
        file_sizes: Dictionary mapping file.id to file size in bytes
    """
    if file_sizes is None:
        file_sizes = {}
    
    # Import format_file_size from helpers
    from app.bot.helpers import format_file_size
    
    builder = InlineKeyboardBuilder()
    
    # Add file buttons - each file as a button
    for file in files:
        # Get file size
        size_bytes = file_sizes.get(file.id, 0)
        size_str = format_file_size(size_bytes)
        
        # Truncate title if too long (max 40 chars for button to leave space for size)
        title = file.title[:40] + "..." if len(file.title) > 40 else file.title
        
        # Format: [file size] file name
        button_text = f"[{size_str}] {title}"
        
        # Telegram button text limit is 64 characters
        if len(button_text) > 64:
            # Adjust title length to fit
            max_title_len = 64 - len(f"[{size_str}] ") - 3  # 3 for "..."
            title = file.title[:max_title_len] + "..."
            button_text = f"[{size_str}] {title}"
        
        builder.button(
            text=button_text,
            callback_data=f"search_file:{file.id}"
        )
    
    # Adjust file buttons first (1 per row)
    builder.adjust(1)
    
    # Add pagination buttons if needed - all three buttons in one row
    if total_pages > 1:
        # Create pagination buttons - always create all three for consistent layout
        prev_button = InlineKeyboardButton(
        text="⬅️" if current_page > 0 else " ",
        callback_data=f"search_page:{current_page - 1}" if current_page > 0 else "noop"
        )

        page_info_button = InlineKeyboardButton(
            text=f"{current_page + 1}/{total_pages}",
            callback_data="search_page_info"
        )

        next_button = InlineKeyboardButton(
            text="➡️" if current_page < total_pages - 1 else " ",
            callback_data=f"search_page:{current_page + 1}" if current_page < total_pages - 1 else "noop"
        )

        
        # Add all three buttons in a single row - Previous (left), Page Info (center), Next (right)
        # Using row() ensures they are side by side horizontally
        builder.row(prev_button, page_info_button, next_button)
    
    return builder.as_markup()