"""
Logging configuration for Ground Control Hub
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from ..core.config import settings


def setup_logging():
    """Configure logging with rotation by date"""

    # Create logs directory
    log_dir = settings.gch_directory / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Log file path with date
    log_file = log_dir / f"gch_{datetime.now().strftime('%Y-%m-%d')}.log"

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()  # Console output
        ]
    )

    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
    logging.getLogger("fastapi").setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")

    return logger