"""Background tasks for file processing"""
import logging
import tempfile
import os
from typing import Optional
from app.bot.main import _bot_instance
from app.models.crud import get_setting, get_file_by_id, update_file_processed_id
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


def process_file_sync(file_id: int, file_telegram_id: str, file_name: Optional[str], title: str):
    """
    Synchronous function to process file (for RQ task queue)
    This function runs in a background worker
    
    Args:
        file_id: Database file ID
        file_telegram_id: Telegram file_id
        file_name: Original filename
        title: File title
    """
    import asyncio
    
    # Create new event loop for this worker
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(process_file_async(file_id, file_telegram_id, file_name, title))
    finally:
        loop.close()


async def process_file_async(file_id: int, file_telegram_id: str, file_name: Optional[str], title: str):
    """
    Async function to process file (download, add thumbnail, rename, re-upload)
    
    Args:
        file_id: Database file ID
        file_telegram_id: Telegram file_id
        file_name: Original filename
        title: File title
    """
    if not _bot_instance:
        logger.error("Bot instance not available for file processing")
        return
    
    async with AsyncSessionLocal() as db:
        try:
            # Get default thumbnail
            global_thumbnail = await get_setting(db, "default_thumbnail_id")
            
            if not global_thumbnail:
                logger.info(f"No default thumbnail set, skipping processing for file {file_id}")
                return
            
            logger.info(f"Processing file {file_id} (telegram_id: {file_telegram_id[:20]}...)")
            
            # Download original file
            doc_file = await _bot_instance.get_file(file_telegram_id)
            
            # Create temporary file for document
            original_filename = file_name or title
            file_ext = os.path.splitext(original_filename)[1] if original_filename else '.pdf'
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_doc:
                doc_path = tmp_doc.name
                await _bot_instance.download_file(doc_file.file_path, doc_path)
            
            # Download thumbnail
            thumb_file = await _bot_instance.get_file(global_thumbnail)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_thumb:
                thumb_path = tmp_thumb.name
                await _bot_instance.download_file(thumb_file.file_path, thumb_path)
            
            # Prepare filename with "- PrimeLingoBot" suffix
            name_without_ext, ext = os.path.splitext(original_filename or title)
            new_filename = f"{name_without_ext} - PrimeLingoBot{ext}"
            
            # Create InputFile objects
            from aiogram.types import FSInputFile
            doc_input = FSInputFile(doc_path, filename=new_filename)
            thumb_input = FSInputFile(thumb_path)
            
            # Get admin ID for sending processed file
            from app.core.config import settings
            admin_id = settings.ADMIN_ID
            
            # Upload processed document with thumbnail
            sent_message = await _bot_instance.send_document(
                chat_id=admin_id,
                document=doc_input,
                caption=f"📚 {title}",
                thumbnail=thumb_input
            )
            
            # Get processed file_id
            processed_file_id = None
            if sent_message.document:
                processed_file_id = sent_message.document.file_id
            
            # Delete the sent message (it was just for getting file_id)
            try:
                await _bot_instance.delete_message(chat_id=admin_id, message_id=sent_message.message_id)
            except Exception:
                pass
            
            # Update database with processed_file_id
            if processed_file_id:
                await update_file_processed_id(db, file_id, processed_file_id)
                logger.info(f"Successfully processed file {file_id}, processed_file_id stored")
            
            # Clean up temporary files
            for path in [doc_path, thumb_path]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except Exception as cleanup_error:
                        logger.warning(f"Error cleaning up temp file {path}: {cleanup_error}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_id}: {e}", exc_info=True)
            raise

