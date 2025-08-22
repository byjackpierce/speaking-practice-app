import logging
from config.settings import settings

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
    return logging.getLogger(__name__)

# Create logger instance
logger = setup_logging()
