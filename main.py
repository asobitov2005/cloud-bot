import asyncio
import logging
import signal
import os
from app.bot.main import main as bot_main
from app.api.main import app
from app.core.config import settings
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_bot():
    """Run the Telegram bot."""
    logger.info("Starting Telegram bot...")
    await bot_main()


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
    server.install_signal_handlers = lambda: None
    await server.serve()


async def main():
    """Run both bot and API concurrently with graceful shutdown."""
    logger.info("=" * 50)
    logger.info("🎓 PrimeLingo Bot Starting...")
    logger.info("=" * 50)

    # Setup signal handlers for immediate shutdown
    def signal_handler():
        logger.info("\n\n👋 Received exit signal. Forcing immediate shutdown...")
        os._exit(0)
    
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Run bot and API concurrently
    bot_task = asyncio.create_task(run_bot())
    api_task = asyncio.create_task(run_api())

    # Wait forever (signal handler will exit)
    await asyncio.gather(bot_task, api_task, return_exceptions=True)

    logger.info("🎓 PrimeLingo Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\n👋 Received exit signal. Exiting...")
    finally:
        # Force exit to ensure all processes are terminated
        logger.info("Forcing process termination...")
        os._exit(0)
