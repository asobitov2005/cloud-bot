import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from app.bot.main import main as bot_main_func
from app.api.main import app
from app.core.config import settings
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global shutdown flag
should_shutdown = False

async def run_bot():
    """Run the Telegram bot with proper signal handling."""
    logger.info("Starting Telegram bot...")
    
    # Import required functions
    from app.bot import init_bot
    from app.bot.main import on_startup, on_shutdown, set_bot_instance
    
    # Initialize bot and dispatcher
    bot, dp = init_bot()
    set_bot_instance(bot)
    
    try:
        # Register aiogram startup/shutdown callbacks
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Start polling WITHOUT signal handling
        await dp.start_polling(
            bot, 
            allowed_updates=dp.resolve_used_update_types(),
            handle_signals=False  # Critical: disable aiogram's signal handling
        )
    except asyncio.CancelledError:
        logger.info("Bot task cancelled, stopping polling...")
        await dp.stop_polling()
        raise
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
        raise
    finally:
        logger.info("Bot cleanup complete")

async def run_api():
    """Run the FastAPI admin panel."""
    logger.info(f"Starting admin panel on {settings.ADMIN_PANEL_HOST}:{settings.ADMIN_PANEL_PORT}...")
    
    config = uvicorn.Config(
        app,
        host=settings.ADMIN_PANEL_HOST,
        port=settings.ADMIN_PANEL_PORT,
        log_level="info",
        lifespan="on",
    )
    server = uvicorn.Server(config)
    
    # Disable uvicorn's signal handlers
    server.install_signal_handlers = lambda: None
    
    try:
        await server.serve()
    except asyncio.CancelledError:
        logger.info("API server cancelled, shutting down...")
        await server.shutdown()
        raise
    finally:
        logger.info("API server cleanup complete")

async def shutdown(tasks):
    """Gracefully shutdown all tasks."""
    logger.info("\n" + "=" * 50)
    logger.info("🛑 Initiating graceful shutdown...")
    logger.info("=" * 50)
    
    # Cancel all tasks
    for task in tasks:
        if not task.done():
            task.cancel()
    
    # Wait for all tasks to complete with timeout
    try:
        await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        logger.warning("Shutdown timeout exceeded, forcing exit")
    
    logger.info("=" * 50)
    logger.info("✅ Shutdown complete")
    logger.info("=" * 50)

async def main():
    """Run both bot and API concurrently with graceful shutdown."""
    logger.info("=" * 50)
    logger.info("🎓 PrimeLingo Bot Starting...")
    logger.info("=" * 50)
    
    # Create tasks
    bot_task = asyncio.create_task(run_bot(), name="bot")
    api_task = asyncio.create_task(run_api(), name="api")
    tasks = [bot_task, api_task]
    
    # Setup signal handlers (Windows-compatible)
    def signal_handler(sig):
        global should_shutdown
        if should_shutdown:
            logger.warning("Second signal received, forcing exit...")
            import os
            os._exit(1)
        
        should_shutdown = True
        try:
            sig_name = signal.Signals(sig).name
        except (ValueError, AttributeError):
            sig_name = str(sig)
        logger.info(f"\n👋 Received signal {sig_name}")
        
        # Create shutdown task
        asyncio.create_task(shutdown(tasks))
    
    # Only add signal handlers on Unix systems (Windows doesn't support add_signal_handler)
    if sys.platform != 'win32':
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
            except NotImplementedError:
                # Fallback if signal handler not supported
                pass
    
    try:
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        # Ensure cleanup
        if not should_shutdown:
            await shutdown(tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Process terminated")