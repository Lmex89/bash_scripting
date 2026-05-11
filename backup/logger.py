import sys
from pathlib import Path

from loguru import logger

from .config import Config


def setup_logging(config: Config) -> None:
    """Setup loguru logging with file and console sinks."""
    log_path = config.log_path
    
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove default logger
    logger.remove()

    # Console sink
    level = "DEBUG" if config.dry_run else config.logging.console_level
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[phase]: <15}</cyan> | <level>{message}</level>",
        level=level,
        colorize=True,
    )

    # File sink
    logger.add(
        str(log_path),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[phase]: <15} | {message}",
        level=config.logging.file_level,
        rotation=config.logging.rotation,
        retention=f"{config.logging.retention_days} days",
        serialize=True,
        backtrace=True,
        diagnose=True,
    )

    if config.dry_run:
        logger.bind(phase="init").warning("DRY-RUN MODE — no changes will be made")
