from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.bot.helpers import safe_answer_callback
from app.bot.keyboards.inline import get_file_actions_keyboard, get_pagination_keyboard
from app.models.crud import (
    get_file_by_id, create_download, increment_download_count
)
import math
import logging

logger = logging.getLogger(__name__)


router = Router()


@router.callback_query(F.data.startswith("download:"))
async def handle_download(callback: CallbackQuery, lang: str, db: AsyncSession, db_user):
    """Handle download button press"""
    # Answer callback IMMEDIATELY to prevent expiration
    await safe_answer_callback(callback)
    
    try:
        file_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        # Query already answered, just send error message
        await callback.message.answer(get_text("delete_not_found", lang))
        return
    
    # Get file (this may take time, but callback is already answered)
    file = await get_file_by_id(db, file_id)
    
    if not file:
        # Query already answered, just send error message
        await callback.message.answer(get_text("delete_not_found", lang))
        return
    
    # Send downloading message to user
    downloading_msg = await callback.message.answer(get_text("downloading", lang))
    
    # Send file - use pre-processed file if available, otherwise process on-the-fly
    try:
        if file.processed_file_id:
            # Use pre-processed file (already has thumbnail and renamed)
            # This is instant - no processing needed!
            logger.info(f"Sending pre-processed file {file.id} with processed_file_id: {file.processed_file_id[:20]}...")
            await callback.message.answer_document(
                document=file.processed_file_id,
                caption=f"<b>{file.title}</b>\n\n🤖 <b>@PRIMELINGOBOT</b>",
                parse_mode="HTML"
            )
            logger.info(f"Successfully sent pre-processed file {file.id}")
        else:
            logger.warning(f"File {file.id} has no processed_file_id, falling back to on-the-fly processing")
            # Fallback: process on-the-fly (for old files or if processing failed during upload)
            from app.models.crud import get_setting
            from app.bot.main import _bot_instance
            from aiogram.types import FSInputFile
            import tempfile
            import os
            
            global_thumbnail = await get_setting(db, "default_thumbnail_id")
            
            if global_thumbnail and _bot_instance:
                # Download and re-upload document with thumbnail
                doc_path = None
                thumb_path = None
                
                try:
                    # Get document file from Telegram
                    doc_file = await _bot_instance.get_file(file.file_id)
                    
                    # Create temporary file for document
                    file_ext = os.path.splitext(file.file_name or 'file')[1] or '.pdf'
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
                    original_filename = file.file_name or file.title
                    name_without_ext, ext = os.path.splitext(original_filename)
                    new_filename = f"{name_without_ext} - PrimeLingoBot{ext}"
                    
                    # Create InputFile objects
                    doc_input = FSInputFile(doc_path, filename=new_filename)
                    thumb_input = FSInputFile(thumb_path)
                    
                    # Send document with thumbnail
                    await callback.message.answer_document(
                        document=doc_input,
                        caption=f"<b>{file.title}</b>\n\n🤖 <b>@PRIMELINGOBOT</b>",
                        thumbnail=thumb_input,
                        parse_mode="HTML"
                    )
                    
                except Exception as download_error:
                    logger.error(f"Error downloading/re-uploading file: {download_error}", exc_info=True)
                    # Fallback: try sending original file without thumbnail
                    await callback.message.answer_document(
                        document=file.file_id,
                        caption=f"<b>{file.title}</b>\n\n🤖 <b>@PRIMELINGOBOT</b>",
                        parse_mode="HTML"
                    )
                finally:
                    # Clean up temporary files
                    for path in [doc_path, thumb_path]:
                        if path and os.path.exists(path):
                            try:
                                os.unlink(path)
                            except Exception as cleanup_error:
                                logger.warning(f"Error cleaning up temp file {path}: {cleanup_error}")
            else:
                # No thumbnail set, send file normally
                await callback.message.answer_document(
                    document=file.file_id,
                    caption=f"<b>{file.title}</b>\n\n🤖 <b>@PRIMELINGOBOT</b>",
                    parse_mode="HTML"
                )
        
        # Record download
        await create_download(db, db_user.id, file.id)
        await increment_download_count(db, file.id)
        
        # Delete downloading message after successful download
        try:
            await downloading_msg.delete()
        except Exception:
            pass  # Ignore errors when deleting message
        
        # Delete the message with download/save buttons to keep chat clean
        try:
            await callback.message.delete()
        except Exception:
            pass  # Ignore errors when deleting message
        
    except Exception as e:
        logger.error(f"Error sending file: {e}", exc_info=True)
        # Try sending without thumbnail if it fails
        try:
            await callback.message.answer_document(
                document=file.file_id,
                caption=f"<b>{file.title}</b>\n\n🤖 <b>@PRIMELINGOBOT</b>",
                parse_mode="HTML"
            )
            # Record download
            await create_download(db, db_user.id, file.id)
            await increment_download_count(db, file.id)
            # Delete downloading message after successful download
            try:
                await downloading_msg.delete()
            except Exception:
                pass  # Ignore errors when deleting message
            
            # Delete the message with download/save buttons to keep chat clean
            try:
                await callback.message.delete()
            except Exception:
                pass  # Ignore errors when deleting message
        except Exception as e2:
            await callback.message.answer(f"🚫 Error sending file: {str(e2)}")
            # Delete downloading message even on error
            try:
                await downloading_msg.delete()
            except Exception:
                pass  # Ignore errors when deleting message
            # Don't delete the button message on error - user might want to try again


