import logging

from pythonjsonlogger.json import JsonFormatter

from app.core.config import get_settings


def setup_logging():
    settings = get_settings()
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)

    log_handler = logging.StreamHandler()
    formatter = JsonFormatter(
        "%(timestamp)s %(levelname)s %(name)s %(request_id)s %(event)s %(message)s",
        timestamp=True,
    )
    log_handler.setFormatter(formatter)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(log_handler)


def get_logger(name: str):
    return logging.getLogger(name)
