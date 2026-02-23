import asyncio
import logging
from app.bot.bot_instance import bot, dp
from app.bot.handlers import base, logging as log_handlers

logger = logging.getLogger(__name__)

async def start_bot():
    """
    Registers routers and starts the Telegram bot polling.
    """
    # Include all routers
    dp.include_router(base.router)
    dp.include_router(log_handlers.router)

    logger.info("Starting Telegram Bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    # For standalone testing
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_bot())
