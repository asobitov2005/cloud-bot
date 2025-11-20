import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from app.bot import init_bot
from app.core.database import init_db
from app.core.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    """Set default bot commands for regular users"""
    # Regular user commands (default for all users)
    user_commands = [
        BotCommand(command="start", description="Start bot"),
        BotCommand(command="help", description="Get help"),
        BotCommand(command="search", description="Search files"),
        BotCommand(command="saved", description="View saved files"),
    ]
    
    # Set default commands for all users
    await bot.set_my_commands(user_commands)
    logger.info("Default user commands set")



async def on_startup(bot: Bot):
    """On startup callback"""
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Setting bot commands...")
    await set_bot_commands(bot)
    
    logger.info("Bot started successfully!")


async def on_shutdown(bot: Bot):
    """On shutdown callback"""
    logger.info("Bot shutting down...")
    await bot.session.close()


# Store bot instance for API access
_bot_instance: Bot = None

def set_bot_instance(bot: Bot):
    """Store bot instance"""
    global _bot_instance
    _bot_instance = bot


async def update_user_commands(telegram_id: int, is_admin: bool):
    """Update commands for a specific user when admin status changes"""
    if _bot_instance is None:
        logger.warning("Bot instance not available, cannot update commands")
        return
    
    from aiogram.types import BotCommand, BotCommandScopeChat
    
    # Regular user commands
    user_commands = [
        BotCommand(command="start", description="Start bot"),
        BotCommand(command="help", description="Get help"),
        BotCommand(command="search", description="Search files"),
        BotCommand(command="saved", description="View saved files"),
    ]
    
    # Admin commands
    admin_commands = user_commands + [
        BotCommand(command="upload", description="Upload file"),
        BotCommand(command="delete", description="Delete file"),
        BotCommand(command="stats", description="View statistics"),
        BotCommand(command="broadcast", description="Broadcast message"),
        BotCommand(command="cancel", description="Cancel operation"),
    ]
    
    try:
        commands = admin_commands if is_admin else user_commands
        await _bot_instance.set_my_commands(
            commands,
            scope=BotCommandScopeChat(chat_id=telegram_id)
        )
        logger.info(f"Updated commands for user {telegram_id}, is_admin={is_admin}")
    except Exception as e:
        logger.error(f"Failed to update commands for user {telegram_id}: {e}")



async def main():
    """Main function to run the bot"""
    # Initialize bot
    bot, dp = init_bot()
    
    # Store bot instance for API access
    set_bot_instance(bot)
    
    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Start polling
    logger.info("Starting bot polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
