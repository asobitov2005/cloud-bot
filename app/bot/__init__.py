from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.core.config import settings
from app.bot.middlewares.user_check import UserCheckMiddleware
from app.bot.middlewares.language import LanguageMiddleware
from app.bot.middlewares.admin_check import AdminCheckMiddleware
from app.bot.middlewares.fsub_check import FSubCheckMiddleware
import logging

logger = logging.getLogger(__name__)

# Try to import RedisStorage, but make it optional
try:
    from aiogram.fsm.storage.redis import RedisStorage
    REDIS_AVAILABLE = True
except ImportError:
    RedisStorage = None
    REDIS_AVAILABLE = False
    logger.warning("Redis storage not available - install redis package for FSM persistence")

# Import handlers
from app.bot.handlers import start, search, downloads, saved_list, help, default, stats
from app.bot.handlers.admin import upload, delete, stats as admin_stats, users, broadcast, settings as admin_settings, fsub


# Initialize bot with optimized configuration
from app.bot.polling import create_optimized_bot_session

# Create optimized session for Bot API requests
session = create_optimized_bot_session()

# Initialize bot with optimized session
bot = Bot(
    token=settings.BOT_TOKEN,
    session=session
)

# Storage will be set up in init_bot() to allow async Redis connection
storage = None  # Will be initialized in init_bot()
dp = None  # Will be initialized in init_bot()


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


async def get_storage():
    """Get FSM storage - Redis if available, otherwise MemoryStorage"""
    if not REDIS_AVAILABLE or RedisStorage is None:
        logger.info("Redis storage not available, using MemoryStorage for FSM")
        return MemoryStorage()
    
    try:
        from app.core.redis_client import get_redis_client
        
        # Try to connect to Redis
        try:
            redis_client = await get_redis_client()
            if redis_client:
                logger.info("Using Redis storage for FSM")
                return RedisStorage(redis=redis_client)
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for FSM storage: {e}. Using MemoryStorage.")
            return MemoryStorage()
    except ImportError:
        logger.warning("Redis client not available, using MemoryStorage for FSM")
        return MemoryStorage()
    
    return MemoryStorage()


def init_bot(with_dispatcher=True):
    """Initialize bot with all components"""
    global storage, dp
    
    # If we only need the bot instance (e.g. for API), skip dispatcher setup
    if not with_dispatcher:
        return bot, None

    # Use MemoryStorage initially - will be upgraded to Redis in on_startup if available
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    setup_middlewares()
    setup_routers()
    return bot, dp


async def upgrade_storage_to_redis():
    """Upgrade FSM storage to Redis if available (called during startup)"""
    global storage, dp
    if not REDIS_AVAILABLE or RedisStorage is None:
        logger.info("Redis storage not available, keeping MemoryStorage")
        return
    
    try:
        redis_storage = await get_storage()
        if RedisStorage and isinstance(redis_storage, RedisStorage):
            # Replace storage
            dp.storage = redis_storage
            storage = redis_storage
            logger.info("FSM storage upgraded to Redis")
    except Exception as e:
        logger.warning(f"Could not upgrade to Redis storage: {e}")
