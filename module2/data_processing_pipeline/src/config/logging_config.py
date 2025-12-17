import logging
import sys


def setup_logging(level: int = logging.INFO):
    """Configure structured logging for the pipeline."""
    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter(
        (
            '{"time": "%(asctime)s", "level": "%(levelname)s", '
            '"name": "%(name)s", "message": "%(message)s"}'
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("Logging is configured")
