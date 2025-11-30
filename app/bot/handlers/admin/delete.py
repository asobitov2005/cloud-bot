from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.models.crud import delete_file


router = Router()


@router.message(Command("delete"))
async def cmd_delete(message: Message, lang: str, db: AsyncSession):
    """Delete file by ID"""
    # Parse file_id from command
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("🚫 Usage: /delete <file_id>")
            return
        
        file_id = int(parts[1])
    except ValueError:
        await message.answer("🚫 Invalid file ID")
        return
    
    # Delete file
    deleted = await delete_file(db, file_id)
    
    if deleted:
        await message.answer(get_text("delete_success", lang))
    else:
        await message.answer(get_text("delete_not_found", lang))
