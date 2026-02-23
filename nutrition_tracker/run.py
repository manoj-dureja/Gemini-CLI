import asyncio
import logging
import uvicorn
from multiprocessing import Process
from app.api.main import app
from app.bot.main import start_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def run_fastapi():
    """
    Runs the FastAPI server using Uvicorn.
    """
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        reload=False  # Disable reload for concurrent run
    )
    server = uvicorn.Server(config)
    logger.info("Starting FastAPI server on http://0.0.0.0:8000...")
    await server.serve()

async def main():
    """
    Launches both the API and the Telegram Bot concurrently.
    """
    # Use gather to run both tasks in the same event loop
    await asyncio.gather(
        run_fastapi(),
        start_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down services...")
