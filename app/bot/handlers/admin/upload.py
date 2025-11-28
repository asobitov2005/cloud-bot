from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text

from app.bot.keyboards.reply import get_main_menu_keyboard
from app.models.crud import create_file
from sqlalchemy.exc import IntegrityError


router = Router()


class UploadStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_title = State()
    waiting_for_tags = State()


@router.message(Command("upload"))
async def cmd_upload(message: Message, state: FSMContext, lang: str):
    """Start file upload process"""
    await message.answer(get_text("upload_send_file", lang))
    await state.set_state(UploadStates.waiting_for_file)


@router.message(UploadStates.waiting_for_file, F.content_type.in_([
    ContentType.DOCUMENT, ContentType.AUDIO, ContentType.VIDEO
]))
async def receive_file(message: Message, state: FSMContext, lang: str):
    """Receive file from admin"""
    # Get file_id based on content type
    if message.document:
        file_id = message.document.file_id
        file_type_content = "document"
    elif message.audio:
        file_id = message.audio.file_id
        file_type_content = "audio"
    elif message.video:
        file_id = message.video.file_id
        file_type_content = "video"
    else:
        await message.answer("❌ Unsupported file type")
        return
    
    # Store file info
    file_name = None
    if message.document:
        file_name = message.document.file_name

    await state.update_data(
        file_id=file_id,
        file_type_content=file_type_content,
        file_name=file_name
    )
    
    # Ask for title
    await message.answer(get_text("upload_enter_title", lang))
    await state.set_state(UploadStates.waiting_for_title)


@router.message(UploadStates.waiting_for_title)
async def receive_title(message: Message, state: FSMContext, lang: str):
    """Receive file title"""
    title = message.text.strip()
    
    # Auto-append " - PrimeLingoBot"
    if not title.endswith(" - PrimeLingoBot"):
        title += " - PrimeLingoBot"
    
    await state.update_data(title=title)
    
    # Ask for tags
    await message.answer(get_text("upload_enter_tags", lang))
    await state.set_state(UploadStates.waiting_for_tags)





@router.message(UploadStates.waiting_for_tags)
async def receive_tags(message: Message, state: FSMContext, lang: str, db: AsyncSession):
    """Receive tags and save to database"""
    tags = message.text.strip() if message.text != "/skip" else None
    
    # Get all data
    data = await state.get_data()
    
    try:
        # Create file in database
        file = await create_file(
            db,
            file_id=data["file_id"],
            title=data["title"],
            file_type="regular", # Default to regular
            type=data["file_type_content"],
            level=data.get("level"),
            tags=tags,
            description=data.get("description"),
            thumbnail_id=None, # Thumbnail removed
            file_name=data.get("file_name")
        )
        
        # Send success message
        success_msg = get_text(
            "upload_success",
            lang,
            title=file.title,
            tags=file.tags or "N/A"
        )
        
        await message.answer(success_msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard(lang))
    except IntegrityError:
        await message.answer("⚠️ This file already exists in the database.", reply_markup=get_main_menu_keyboard(lang))
    except Exception as e:
        await message.answer(f"❌ Error saving file: {e}", reply_markup=get_main_menu_keyboard(lang))
    
    await state.clear()


@router.message(Command("cancel"))
async def cancel_upload(message: Message, state: FSMContext, lang: str):
    """Cancel upload process"""
    await state.clear()
    await message.answer(get_text("upload_cancelled", lang))
