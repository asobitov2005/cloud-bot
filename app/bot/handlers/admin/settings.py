from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.models.crud import set_setting, delete_setting
import logging

logger = logging.getLogger(__name__)
router = Router()


class SettingsStates(StatesGroup):
    waiting_for_thumbnail = State()


@router.message(Command("setthumb"))
@router.message(Command("set_thumb"))
async def cmd_setthumb(message: Message, state: FSMContext, lang: str):
    """Start default thumbnail setup"""
    await message.answer(get_text("send_default_thumbnail", lang))
    await state.set_state(SettingsStates.waiting_for_thumbnail)


@router.message(SettingsStates.waiting_for_thumbnail, F.content_type.in_([ContentType.PHOTO, ContentType.DOCUMENT]))
async def receive_default_thumbnail(message: Message, state: FSMContext, db: AsyncSession, lang: str):
    """Receive and save default thumbnail - accepts both photo and document"""
    thumbnail_id = None
    
    # Prefer photo over document for better compatibility
    if message.photo:
        # Get largest photo (best quality)
        photo = message.photo[-1]
        thumbnail_id = photo.file_id
        logger.info(f"Thumbnail set from photo: {thumbnail_id}")
    elif message.document:
        # If sent as document, try to use its thumbnail
        # Note: For best results, send thumbnail as photo, not document
        if message.document.thumbnail:
            thumbnail_id = message.document.thumbnail.file_id
            logger.info(f"Thumbnail set from document thumbnail: {thumbnail_id}")
        else:
            # Document without thumbnail - use document file_id
            # This might not work perfectly with answer_document thumb parameter
            thumbnail_id = message.document.file_id
            logger.warning(f"Using document file_id as thumbnail (may not work): {thumbnail_id}")
            await message.answer("⚠️ For best results, send the thumbnail as a photo (not as a file). Using document file_id which may not work correctly.")
    
    if not thumbnail_id:
        await message.answer("🚫 Could not extract thumbnail. Please send a photo or image file.")
        return
    
    # Save to settings
    await set_setting(db, "default_thumbnail_id", thumbnail_id)
    
    await message.answer(get_text("default_thumbnail_set", lang))
    await state.clear()


@router.message(Command("delthumb"))
@router.message(Command("del_thumb"))
async def cmd_delthumb(message: Message, db: AsyncSession, lang: str):
    """Delete default thumbnail"""
    await delete_setting(db, "default_thumbnail_id")
    await message.answer(get_text("default_thumbnail_deleted", lang))


@router.message(Command("cancel"))
async def cancel_settings(message: Message, state: FSMContext, lang: str):
    """Cancel settings operation"""
    await state.clear()
    await message.answer(get_text("upload_cancelled", lang))
