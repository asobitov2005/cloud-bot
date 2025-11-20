from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.bot.keyboards.reply import get_file_type_keyboard
from app.models.crud import create_file


router = Router()


class UploadStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_title = State()
    waiting_for_thumbnail = State()
    waiting_for_tags = State()
    waiting_for_file_type = State()


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
    await state.update_data(
        file_id=file_id,
        file_type_content=file_type_content
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
    
    # Ask for thumbnail
    await message.answer(get_text("upload_send_thumbnail", lang))
    await state.set_state(UploadStates.waiting_for_thumbnail)


@router.message(UploadStates.waiting_for_thumbnail, F.photo)
async def receive_thumbnail(message: Message, state: FSMContext, lang: str):
    """Receive thumbnail image"""
    # Get largest photo
    photo = message.photo[-1]
    thumbnail_id = photo.file_id
    
    await state.update_data(thumbnail_id=thumbnail_id)
    
    # Ask for tags
    await message.answer(get_text("upload_enter_tags", lang))
    await state.set_state(UploadStates.waiting_for_tags)


@router.message(UploadStates.waiting_for_thumbnail, Command("skip"))
async def skip_thumbnail(message: Message, state: FSMContext, lang: str):
    """Skip thumbnail"""
    await state.update_data(thumbnail_id=None)
    
    # Ask for tags
    await message.answer(get_text("upload_enter_tags", lang))
    await state.set_state(UploadStates.waiting_for_tags)


@router.message(UploadStates.waiting_for_tags)
async def receive_tags(message: Message, state: FSMContext, lang: str):
    """Receive tags"""
    tags = message.text.strip() if message.text != "/skip" else None
    
    await state.update_data(tags=tags)
    
    # Ask for file type
    await message.answer(get_text("upload_file_type", lang), reply_markup=get_file_type_keyboard())
    await state.set_state(UploadStates.waiting_for_file_type)


@router.message(UploadStates.waiting_for_file_type, F.text.in_(["📄 Regular", "📝 Mock Test"]))
async def receive_file_type(message: Message, state: FSMContext, lang: str, db: AsyncSession):
    """Receive file type and save to database"""
    file_type = "regular" if message.text == "📄 Regular" else "mock_test"
    
    # Get all data
    data = await state.get_data()
    
    # Create file in database
    file = await create_file(
        db,
        file_id=data["file_id"],
        title=data["title"],
        file_type=file_type,
        type=data["file_type_content"],
        level=data.get("level"),
        tags=data.get("tags"),
        description=data.get("description"),
        thumbnail_id=data.get("thumbnail_id")
    )
    
    # Send success message
    success_msg = get_text(
        "upload_success",
        lang,
        title=file.title,
        tags=file.tags or "N/A"
    )
    
    await message.answer(success_msg, parse_mode="HTML")
    await state.clear()


@router.message(Command("cancel"))
async def cancel_upload(message: Message, state: FSMContext, lang: str):
    """Cancel upload process"""
    await state.clear()
    await message.answer(get_text("upload_cancelled", lang))
