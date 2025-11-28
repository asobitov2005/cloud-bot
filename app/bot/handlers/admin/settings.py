from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.models.crud import set_setting, delete_setting

router = Router()


class SettingsStates(StatesGroup):
    waiting_for_thumbnail = State()


@router.message(Command("setthumb"))
async def cmd_setthumb(message: Message, state: FSMContext, lang: str):
    """Start default thumbnail setup"""
    await message.answer(get_text("send_default_thumbnail", lang))
    await state.set_state(SettingsStates.waiting_for_thumbnail)


@router.message(SettingsStates.waiting_for_thumbnail, F.photo)
async def receive_default_thumbnail(message: Message, state: FSMContext, db: AsyncSession, lang: str):
    """Receive and save default thumbnail"""
    # Get largest photo
    photo = message.photo[-1]
    thumbnail_id = photo.file_id
    
    # Save to settings
    await set_setting(db, "default_thumbnail_id", thumbnail_id)
    
    await message.answer(get_text("default_thumbnail_set", lang))
    await state.clear()


@router.message(Command("delthumb"))
async def cmd_delthumb(message: Message, db: AsyncSession, lang: str):
    """Delete default thumbnail"""
    await delete_setting(db, "default_thumbnail_id")
    await message.answer(get_text("default_thumbnail_deleted", lang))


@router.message(Command("cancel"))
async def cancel_settings(message: Message, state: FSMContext, lang: str):
    """Cancel settings operation"""
    await state.clear()
    await message.answer(get_text("upload_cancelled", lang))
