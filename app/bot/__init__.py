from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.core.config import settings
from app.bot.middlewares.user_check import UserCheckMiddleware
from app.bot.middlewares.language import LanguageMiddleware
from app.bot.middlewares.admin_check import AdminCheckMiddleware
from app.bot.middlewares.fsub_check import FSubCheckMiddleware

# Import handlers
from app.bot.handlers import start, search, downloads, saved_list, help, default, stats
from app.bot.handlers.admin import upload, delete, stats as admin_stats, users, broadcast, settings as admin_settings, fsub


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
    
    # Force subscribe check middleware (after user check, before admin check)
    dp.message.middleware(FSubCheckMiddleware())
    dp.callback_query.middleware(FSubCheckMiddleware())


def setup_routers():
    """Setup routers"""
    # User handlers
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(downloads.router)
    dp.include_router(saved_list.router)
    dp.include_router(help.router)
    dp.include_router(stats.router)  # Stats command available to all users
    
    # Admin handlers (with admin check middleware and specific permissions)
    # These must be registered BEFORE the default handler so state handlers work correctly
    upload.router.message.middleware(AdminCheckMiddleware(required_permission="upload"))
    delete.router.message.middleware(AdminCheckMiddleware(required_permission="delete"))
    admin_stats.router.message.middleware(AdminCheckMiddleware(required_permission="stats"))
    users.router.message.middleware(AdminCheckMiddleware(required_permission="users"))
    broadcast.router.message.middleware(AdminCheckMiddleware(required_permission="broadcast"))
    admin_settings.router.message.middleware(AdminCheckMiddleware(required_permission="settings"))
    fsub.router.message.middleware(AdminCheckMiddleware(required_permission="fsub"))
    fsub.router.callback_query.middleware(AdminCheckMiddleware(required_permission="fsub"))
    
    dp.include_router(upload.router)
    dp.include_router(delete.router)
    dp.include_router(admin_stats.router)
    dp.include_router(users.router)
    dp.include_router(broadcast.router)
    dp.include_router(admin_settings.router)
    dp.include_router(fsub.router)
    
    # Default/catch-all handler (must be last to catch unhandled messages)
    dp.include_router(default.router)


def init_bot():
    """Initialize bot with all components"""
    setup_middlewares()
    setup_routers()
    return bot, dp
