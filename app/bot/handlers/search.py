from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.bot.keyboards.inline import get_file_actions_keyboard, get_pagination_keyboard, get_search_results_keyboard
from app.models.crud import search_files, get_file_by_id
import math
import time
import logging

logger = logging.getLogger(__name__)

router = Router()


class SearchStates(StatesGroup):
    waiting_for_query = State()


# Store search results temporarily
search_cache = {}


@router.message(Command("search"))
@router.message(F.text.in_([
    "🔍 Qidiruv", "🔍 Search", "🔍 Поиск"
]))
async def start_search(message: Message, state: FSMContext, lang: str):
    """Handle search button press"""
    await message.answer(get_text("enter_search_query", lang), parse_mode="HTML")
    await state.set_state(SearchStates.waiting_for_query)


@router.message(SearchStates.waiting_for_query, F.text)
async def process_search(message: Message, state: FSMContext, lang: str, db: AsyncSession):
    """Process search query"""
    # Skip if this is a command
    if message.text.startswith("/") or message.text.startswith("!"):
        # Clear search state when command is sent
        await state.clear()
        return
    
    # Check if this is a button click (reply keyboard button)
    # Get button texts for current language
    btn_search = get_text("btn_search", lang)
    btn_my_list = get_text("btn_my_list", lang)
    btn_help = get_text("btn_help", lang)
    btn_change_language = get_text("btn_change_language", lang)
    
    # If user clicked a button, clear search state and let other handlers process it
    if message.text in [btn_search, btn_my_list, btn_help, btn_change_language]:
        await state.clear()
        return
    
    query = message.text.strip()
    
    if not query:
        await message.answer(get_text("enter_search_query", lang), parse_mode="HTML")
        return
    
    # Send searching message
    searching_msg = await message.answer(get_text("searching", lang))
    start_time = time.time()
    
    # Search files - get all results (no limit for pagination)
    files = await search_files(db, query, file_type=None, skip=0, limit=1000)
    
    # Calculate time spent
    time_spent = round(time.time() - start_time, 2)
    
    # Delete searching message
    try:
        await searching_msg.delete()
    except Exception:
        pass
    
    if not files:
        await message.answer(get_text("no_results", lang))
        # Keep state active so user can search again without clicking button
        # Don't clear state - user can send another search query
        return
    
    # Get file sizes from Telegram
    file_sizes = {}
    try:
        from app.bot.main import _bot_instance
        if _bot_instance:
            for file in files:
                try:
                    file_info = await _bot_instance.get_file(file.file_id)
                    file_sizes[file.id] = file_info.file_size or 0
                except Exception as e:
                    logger.warning(f"Could not get file size for file {file.id}: {e}")
                    file_sizes[file.id] = 0
    except Exception as e:
        logger.warning(f"Could not get bot instance for file sizes: {e}")
    
    # Store search results in cache
    user_id = message.from_user.id
    search_cache[user_id] = {
        "query": query,
        "files": files,
        "file_sizes": file_sizes,
        "page": 0,
        "time_spent": time_spent
    }
    
    # Send results as inline buttons
    await send_search_results(message, files, 0, query, time_spent, lang, db, file_sizes)
    await state.clear()


@router.callback_query(F.data.startswith("search_file:"))
async def handle_search_file(callback: CallbackQuery, lang: str, db: AsyncSession):
    """Handle when user clicks on a search result file"""
    try:
        file_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(get_text("delete_not_found", lang), show_alert=True)
        return
    
    # Get file
    file = await get_file_by_id(db, file_id)
    
    if not file:
        await callback.answer(get_text("delete_not_found", lang), show_alert=True)
        return
    
    # Answer callback to stop button animation
    await callback.answer()
    
    # Build file info text
    text = f"<b>{file.title}</b>\n"
    
    if file.level:
        text += f"📊 {get_text('level', lang)}: {file.level}\n"
    
    if file.description:
        text += f"\n{file.description}\n"
    
    # Send file info with download and save buttons
    keyboard = get_file_actions_keyboard(file.id, lang)
    
    await callback.message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("search_page:"))
async def handle_search_pagination(callback: CallbackQuery, lang: str, db: AsyncSession):
    """Handle search results pagination"""
    try:
        page = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer()
        return
    
    # Get search cache
    user_id = callback.from_user.id
    if user_id not in search_cache:
        await callback.answer(get_text("no_results", lang), show_alert=True)
        return
    
    cache_data = search_cache[user_id]
    files = cache_data["files"]
    file_sizes = cache_data.get("file_sizes", {})
    query = cache_data["query"]
    time_spent = cache_data.get("time_spent", 0)
    
    # Update page in cache
    search_cache[user_id]["page"] = page
    
    # Send updated results
    try:
        # Edit the message with new results
        total_pages = math.ceil(len(files) / 3)
        start_idx = page * 3
        end_idx = start_idx + 3
        page_files = files[start_idx:end_idx]
        
        # Build header with search info
        header_text = (
            f"<b>{get_text('search_result_for', lang, query=query)}</b>\n\n"
            f"<b>{get_text('result_shown_in', lang, time=time_spent)}</b>\n\n"
        )
        
        # Create keyboard with file buttons
        keyboard = get_search_results_keyboard(page_files, page, total_pages, lang, file_sizes)
        
        await callback.message.edit_text(
            header_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(get_text("no_results", lang), show_alert=True)


@router.callback_query(F.data == "search_page_info")
async def handle_search_page_info(callback: CallbackQuery):
    """Handle search page info click (no action needed)"""
    await callback.answer()


async def send_search_results(message: Message, files: list, page: int, 
                              query: str, time_spent: float, lang: str, db: AsyncSession, 
                              file_sizes: dict = None):
    """Send search results as inline buttons with pagination"""
    if file_sizes is None:
        file_sizes = {}
    
    total_pages = math.ceil(len(files) / 3)  # Show 10 results per page
    start_idx = page * 3
    end_idx = start_idx + 3
    page_files = files[start_idx:end_idx]
    
    # Build header with search info
    header_text = (
        f"<b>{get_text('search_result_for', lang, query=query)}</b>\n\n"
        f"<b>{get_text('result_shown_in', lang, time=time_spent)}</b>\n\n"
    )
    
    # Create keyboard with file buttons
    keyboard = get_search_results_keyboard(page_files, page, total_pages, lang, file_sizes)
    
    # Send results as single message with inline buttons
    await message.answer(
        header_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
