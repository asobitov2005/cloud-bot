from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.core.config import settings
from app.bot.middlewares.user_check import UserCheckMiddleware
from app.bot.middlewares.language import LanguageMiddleware
from app.bot.middlewares.admin_check import AdminCheckMiddleware

# Import handlers
from app.bot.handlers import start, search, downloads, saved_list, mock_tests, help
from app.bot.handlers.admin import upload, delete, stats, users, broadcast


# Initialize bot and dispatcher
bot = Bot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


def setup_middlewares():
    """Setup middlewares"""
    # User check middleware (must be first)
    dp.message.middleware(UserCheckMiddleware())
    dp.callback_query.middleware(UserCheckMiddleware())
    
    # Language middleware
    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())


def setup_routers():
    """Setup routers"""
    # User handlers
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(downloads.router)
    dp.include_router(saved_list.router)
    dp.include_router(mock_tests.router)
    dp.include_router(help.router)
    
    # Admin handlers (with admin check middleware)
    upload.router.message.middleware(AdminCheckMiddleware())
    delete.router.message.middleware(AdminCheckMiddleware())
    stats.router.message.middleware(AdminCheckMiddleware())
    users.router.message.middleware(AdminCheckMiddleware())
    broadcast.router.message.middleware(AdminCheckMiddleware())
    
    dp.include_router(upload.router)
    dp.include_router(delete.router)
    dp.include_router(stats.router)
    dp.include_router(users.router)
    dp.include_router(broadcast.router)


def init_bot():
    """Initialize bot with all components"""
    setup_middlewares()
    setup_routers()
    return bot, dp
