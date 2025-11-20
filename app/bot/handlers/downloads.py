from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.bot.keyboards.inline import get_file_actions_keyboard, get_pagination_keyboard
from app.models.crud import (
    get_file_by_id, create_download, increment_download_count,
    get_user_downloads
)
import math


router = Router()


@router.callback_query(F.data.startswith("download:"))
async def handle_download(callback: CallbackQuery, lang: str, db: AsyncSession, db_user):
    """Handle download button press"""
    file_id = int(callback.data.split(":")[1])
    
    # Get file
    file = await get_file_by_id(db, file_id)
    
    if not file:
        await callback.answer(get_text("delete_not_found", lang), show_alert=True)
        return
    
    # Send downloading message
    await callback.answer(get_text("downloading", lang))
    
    # Send file
    try:
        await callback.message.answer_document(
            document=file.file_id,
            caption=f"📚 {file.title}"
        )
        
        # Record download
        await create_download(db, db_user.id, file.id)
        await increment_download_count(db, file.id)
        
    except Exception as e:
        await callback.message.answer(f"❌ Error sending file: {str(e)}")


@router.message(F.text.in_([
    "📥 Yuklab olinganlar", "📥 My Downloads", "📥 Мои загрузки"
]))
async def show_my_downloads(message: Message, lang: str, db: AsyncSession, db_user):
    """Show user's download history"""
    # Get user downloads
    downloads = await get_user_downloads(db, db_user.id, skip=0, limit=50)
    
    if not downloads:
        await message.answer(get_text("no_downloads", lang))
        return
    
    # Send header
    await message.answer(get_text("my_downloads_title", lang))
    
    # Send each downloaded file
    for download in downloads[:5]:  # Show first 5
        file = download.file
        
        # Build file info text
        text = f"📚 <b>{file.title}</b>\n"
        
        if file.level:
            text += f"📊 {get_text('level', lang)}: {file.level}\n"
        
        text += f"📅 {download.downloaded_at.strftime('%Y-%m-%d %H:%M')}"
        
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
    if len(downloads) > 5:
        total_pages = math.ceil(len(downloads) / 5)
        pagination_kb = get_pagination_keyboard(0, total_pages, "downloads", lang)
        await message.answer(
            get_text("page_info", lang, current=1, total=total_pages),
            reply_markup=pagination_kb
        )
