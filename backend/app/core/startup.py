import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def startup_event(app):
    logger.info("Starting up the application...")
    # Add any startup logic here
    logger.info("Application started successfully.")
    
async def shutdown_event(app):
    logger.info("Shutting down the application...")
    # Add any shutdown logic here
    logger.info("Application shut down successfully.")