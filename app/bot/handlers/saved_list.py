from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.bot.keyboards.inline import get_file_actions_keyboard, get_pagination_keyboard
from app.bot.helpers import safe_answer_callback
from app.models.crud import (
    add_to_saved_list, remove_from_saved_list, get_user_saved_files,
    get_file_by_id
)
import math


router = Router()


@router.callback_query(F.data.startswith("save:"))
async def handle_save_to_list(callback: CallbackQuery, lang: str, db: AsyncSession, db_user):
    """Handle save to list button press"""
    try:
        file_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await safe_answer_callback(callback, get_text("delete_not_found", lang), show_alert=True)
        return
    
    # Add to saved list (quick operation, should complete before callback expires)
    saved = await add_to_saved_list(db, db_user.id, file_id)
    
    # Answer callback with alert AFTER we know the result
    if saved:
        # Show success alert
        await safe_answer_callback(callback, get_text("file_saved", lang), show_alert=True)
    else:
        # Show already saved alert
        await safe_answer_callback(callback, get_text("already_saved", lang), show_alert=True)


@router.callback_query(F.data.startswith("remove:"))
async def handle_remove_from_list(callback: CallbackQuery, lang: str, db: AsyncSession, db_user):
    """Handle remove from list button press"""
    try:
        file_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await safe_answer_callback(callback, "🚫 Error", show_alert=True)
        return
    
    # Remove from saved list first (quick operation)
    removed = await remove_from_saved_list(db, db_user.id, file_id)
    
    # Answer callback with alert AFTER we know the result
    if removed:
        # Answer callback first to stop loading animation
        await safe_answer_callback(callback, get_text("file_removed", lang), show_alert=True)
        # Delete the message
        try:
            await callback.message.delete()
        except:
            pass
    else:
        # Show error alert
        await safe_answer_callback(callback, "🚫 Error", show_alert=True)


@router.message(Command("saved"))
@router.message(F.text.in_([
    "📁 Mening ro'yxatim", "📁 My List", "📁 Мой список"
]))
async def show_my_list(message: Message, lang: str, db: AsyncSession, db_user):
    """Show user's saved files"""
    await show_saved_list_page(message, lang, db, db_user.id, page=0)


@router.callback_query(F.data.startswith("saved_page:"))
async def handle_saved_pagination(callback: CallbackQuery, lang: str, db: AsyncSession, db_user):
    """Handle saved list pagination"""
    page = int(callback.data.split(":")[1])
    await show_saved_list_page(callback.message, lang, db, db_user.id, page=page, is_edit=True)


async def show_saved_list_page(message: Message, lang: str, db: AsyncSession, user_id: int, page: int = 0, is_edit: bool = False):
    """Show specific page of saved list"""
    ITEMS_PER_PAGE = 10
    
    # Get user saved files
    saved_files = await get_user_saved_files(db, user_id, skip=page * ITEMS_PER_PAGE, limit=ITEMS_PER_PAGE)
    
    # Get total count for pagination
    # We need a count function in crud, but for now we can fetch all (inefficient but works for small lists)
    # Or better, let's just fetch a large number to check if there are more
    # Ideally we should add get_user_saved_count to crud.py
    # For now, let's assume if we got ITEMS_PER_PAGE, there might be more. 
    # But to do proper numbered pagination we need total count.
    # Let's add a simple count query here or in crud.
    
    # Quick fix: get all saved files to count (temporary, should be optimized)
    all_saved = await get_user_saved_files(db, user_id, skip=0, limit=1000)
    total_items = len(all_saved)
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
    
    if not saved_files and page == 0:
        if is_edit:
            await message.edit_text(get_text("no_saved_files", lang))
        else:
            await message.answer(get_text("no_saved_files", lang))
        return
    
    # Send header message
    header_text = f"{get_text('my_list_title', lang)}\n"
    if total_pages > 1:
        header_text += f"\n{get_text('page_info', lang, current=page + 1, total=total_pages)}"
    
    # Pagination keyboard
    keyboard = None
    if total_pages > 1:
        keyboard = get_pagination_keyboard(page, total_pages, "saved", lang)
    
    if is_edit:
        # If editing, update the header message
        await message.edit_text(header_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        # Send header message
        await message.answer(header_text, reply_markup=keyboard, parse_mode="HTML")
    
    # Send each file as a separate message with inline buttons
    for i, saved in enumerate(saved_files):
        file = saved.file
        
        # Build file info text
        text = f"<b>{file.title}</b>"
        if file.level:
            text += f"\n📊 {get_text('level', lang)}: {file.level}"
        if file.description:
            text += f"\n\n{file.description}"
        
        # Get keyboard with download and remove buttons
        file_keyboard = get_file_actions_keyboard(file.id, lang, show_remove=True)
        
        # Send file info with buttons
        await message.answer(text, reply_markup=file_keyboard, parse_mode="HTML")


@router.message(F.text.regexp(r"^/get_(\d+)$"))
async def handle_get_file_command(message: Message, lang: str, db: AsyncSession):
    """Handle /get_ID command"""
    file_id = int(message.text.split("_")[1])
    file = await get_file_by_id(db, file_id)
    
    if not file:
        await message.answer(get_text("delete_not_found", lang))
        return
        
    # Send file
    caption = f"📚 <b>{file.title}</b>\n"
    if file.description:
        caption += f"\n{file.description}\n"
    
    keyboard = get_file_actions_keyboard(file.id, lang, show_remove=True)
    
    # Send file info (thumbnail removed from message as it's already on the file)
    await message.answer(caption, reply_markup=keyboard, parse_mode="HTML")
    
    # Send actual file - REMOVED as per user request (user can click download button)
    # await message.answer_document(file.file_id)


@router.message(F.text.regexp(r"^/del_(\d+)$"))
async def handle_del_file_command(message: Message, lang: str, db: AsyncSession, db_user):
    """Handle /del_ID command"""
    file_id = int(message.text.split("_")[1])
    
    removed = await remove_from_saved_list(db, db_user.id, file_id)
    
    if removed:
        await message.answer(get_text("file_removed", lang))
        # Refresh list? Maybe just let user click "My List" again or refresh current page if they are on it.
        # Ideally we should refresh the list message if we knew which one it was.
    else:
        await message.answer("🚫 Error or not found")
