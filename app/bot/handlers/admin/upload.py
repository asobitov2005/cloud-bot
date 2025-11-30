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
        await message.answer("🚫 Unsupported file type")
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


@router.message(UploadStates.waiting_for_title, F.text)
async def receive_title(message: Message, state: FSMContext, lang: str):
    """Receive file title"""
    # Skip if this is a command
    if message.text.startswith("/"):
        return
    
    title = message.text.strip()
    
    # Auto-append " - PrimeLingoBot"
    if not title.endswith(" - PrimeLingoBot"):
        title += " - PrimeLingoBot"
    
    await state.update_data(title=title)
    
    # Ask for tags
    await message.answer(get_text("upload_enter_tags", lang))
    await state.set_state(UploadStates.waiting_for_tags)





@router.message(UploadStates.waiting_for_tags, F.text)
async def receive_tags(message: Message, state: FSMContext, lang: str, db: AsyncSession):
    """Receive tags and save to database"""
    # Skip if this is a command (except /skip)
    if message.text.startswith("/") and message.text != "/skip":
        return
    
    tags = message.text.strip() if message.text != "/skip" else None
    
    # Get all data
    data = await state.get_data()
    
    try:
        # Process file: download, add thumbnail, rename, and re-upload
        processed_file_id = None
        from app.models.crud import get_setting
        from app.bot.main import _bot_instance
        from aiogram.types import FSInputFile
        import tempfile
        import os
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get global thumbnail
        global_thumbnail = await get_setting(db, "default_thumbnail_id")
        
        if global_thumbnail and _bot_instance:
            # Send processing message
            processing_msg = await message.answer("⏳ Processing file (adding thumbnail and renaming)...")
            
            try:
                # Get document file from Telegram
                doc_file = await _bot_instance.get_file(data["file_id"])
                
                # Create temporary file for document
                original_filename = data.get("file_name") or data["title"]
                file_ext = os.path.splitext(original_filename)[1] or '.pdf'
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_doc:
                    doc_path = tmp_doc.name
                    await _bot_instance.download_file(doc_file.file_path, doc_path)
                
                # Get thumbnail file from Telegram
                thumb_file = await _bot_instance.get_file(global_thumbnail)
                
                # Create temporary file for thumbnail
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_thumb:
                    thumb_path = tmp_thumb.name
                    await _bot_instance.download_file(thumb_file.file_path, thumb_path)
                
                # Prepare filename with "- PrimeLingoBot" suffix
                name_without_ext, ext = os.path.splitext(original_filename)
                new_filename = f"{name_without_ext} - PrimeLingoBot{ext}"
                
                # Create InputFile objects
                doc_input = FSInputFile(doc_path, filename=new_filename)
                thumb_input = FSInputFile(thumb_path)
                
                # Upload processed document with thumbnail
                # Send it to the admin's chat to get the processed file_id
                sent_message = await _bot_instance.send_document(
                    chat_id=message.from_user.id,
                    document=doc_input,
                    caption=f"📚 {data['title']}",
                    thumbnail=thumb_input
                )
                
                # Get the processed file_id from the sent message
                if sent_message.document:
                    processed_file_id = sent_message.document.file_id
                    
                # Delete the processing message sent to admin (it was just for getting file_id)
                try:
                    await _bot_instance.delete_message(chat_id=message.from_user.id, message_id=sent_message.message_id)
                except:
                    pass
                
                # Clean up temporary files
                for path in [doc_path, thumb_path]:
                    if path and os.path.exists(path):
                        try:
                            os.unlink(path)
                        except Exception as cleanup_error:
                            logger.warning(f"Error cleaning up temp file {path}: {cleanup_error}")
                
                # Delete processing message
                try:
                    await processing_msg.delete()
                except:
                    pass
                    
            except Exception as process_error:
                logger.error(f"Error processing file: {process_error}", exc_info=True)
                # Continue without processed file - will process on download
                try:
                    await processing_msg.delete()
                except:
                    pass
        
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
            file_name=data.get("file_name"),
            processed_file_id=processed_file_id
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
        await message.answer(f"🚫 Error saving file: {e}", reply_markup=get_main_menu_keyboard(lang))
    
    await state.clear()


@router.message(Command("cancel"))
async def cancel_upload(message: Message, state: FSMContext, lang: str):
    """Cancel upload process"""
    await state.clear()
    await message.answer(get_text("upload_cancelled", lang))
