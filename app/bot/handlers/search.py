from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.bot.keyboards.inline import get_file_actions_keyboard, get_pagination_keyboard
from app.models.crud import search_files
import math


router = Router()


class SearchStates(StatesGroup):
    waiting_for_query = State()


# Store search results temporarily
search_cache = {}


@router.message(F.text.in_([
    "🔍 Qidiruv", "🔍 Search", "🔍 Поиск"
]))
async def start_search(message: Message, state: FSMContext, lang: str):
    """Handle search button press"""
    await message.answer(get_text("enter_search_query", lang))
    await state.set_state(SearchStates.waiting_for_query)


@router.message(SearchStates.waiting_for_query)
async def process_search(message: Message, state: FSMContext, lang: str, db: AsyncSession):
    """Process search query"""
    query = message.text.strip()
    
    if not query:
        await message.answer(get_text("enter_search_query", lang))
        return
    
    # Search files
    files = await search_files(db, query, file_type=None, skip=0, limit=5)
    
    if not files:
        await message.answer(get_text("no_results", lang))
        await state.clear()
        return
    
    # Store search results in cache
    user_id = message.from_user.id
    search_cache[user_id] = {
        "query": query,
        "files": files,
        "page": 0
    }
    
    # Send results
    await send_search_results(message, files, 0, lang, db)
    await state.clear()


async def send_search_results(message: Message, files: list, page: int, 
                              lang: str, db: AsyncSession):
    """Send search results with pagination"""
    total_pages = math.ceil(len(files) / 5)
    start_idx = page * 5
    end_idx = start_idx + 5
    page_files = files[start_idx:end_idx]
    
    # Send header
    await message.answer(get_text("search_results", lang))
    
    # Send each file
    for file in page_files:
        # Build file info text
        text = f"📚 <b>{file.title}</b>\n"
        
        if file.level:
            text += f"📊 {get_text('level', lang)}: {file.level}\n"
        
        if file.description:
            text += f"\n{file.description}\n"
        
        if file.tags:
            text += f"\n🏷 {file.tags}"
        
        
        # Send with thumbnail if available
        keyboard = get_file_actions_keyboard(file.id, lang)
        
        # Get appropriate thumbnail (file's own or default if ≤20MB)
        from app.bot.helpers import get_thumbnail_for_file
        from app.bot.main import _bot_instance
        
        thumbnail_to_use = await get_thumbnail_for_file(
            _bot_instance, 
            file.file_id, 
            file.thumbnail_id, 
            db
        )
        
        if thumbnail_to_use:
            try:
                await message.answer_photo(
                    photo=thumbnail_to_use,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except:
                # If thumbnail fails, send as text
                await message.answer(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        else:
            await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    
    # Send pagination if needed
    if total_pages > 1:
        pagination_kb = get_pagination_keyboard(page, total_pages, "search", lang)
        await message.answer(
            get_text("page_info", lang, current=page + 1, total=total_pages),
            reply_markup=pagination_kb
        )
