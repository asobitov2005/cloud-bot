from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.bot.keyboards.inline import get_file_actions_keyboard, get_pagination_keyboard
from app.models.crud import get_all_files
import math


router = Router()


@router.message(F.text.in_([
    "📝 Mock testlar", "📝 Mock tests", "📝 Пробные тесты"
]))
async def show_mock_tests(message: Message, lang: str, db: AsyncSession):
    """Show mock tests"""
    # Get mock test files
    files = await get_all_files(db, file_type="mock_test", skip=0, limit=50)
    
    if not files:
        await message.answer(get_text("no_mock_tests", lang))
        return
    
    # Send header
    await message.answer(get_text("mock_tests_title", lang))
    
    # Send each mock test
    for file in files[:5]:  # Show first 5
        # Build file info text
        text = f"📝 <b>{file.title}</b>\n"
        
        if file.level:
            text += f"📊 {get_text('level', lang)}: {file.level}\n"
        
        if file.description:
            text += f"\n{file.description}\n"
        
        if file.tags:
            text += f"\n🏷 {file.tags}"
        
        # Send with actions
        keyboard = get_file_actions_keyboard(file.id, lang)
        
        if file.thumbnail_id:
            try:
                await message.answer_photo(
                    photo=file.thumbnail_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except:
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
    
    # Show pagination if more than 5
    if len(files) > 5:
        total_pages = math.ceil(len(files) / 5)
        pagination_kb = get_pagination_keyboard(0, total_pages, "mock_tests", lang)
        await message.answer(
            get_text("page_info", lang, current=1, total=total_pages),
            reply_markup=pagination_kb
        )
