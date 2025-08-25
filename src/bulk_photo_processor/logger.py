from pathlib import Path
import logging

def setup_logger(logger_name=None, log_file_path=None):
    default_logger = False
    default_file_path = False
    # Fallbacks if config values are missing
    if logger_name is None:
        logger_name = 'bulk_photo_processor'
        default_logger = True
    if log_file_path is None:
        log_file_path = './logs/default.log'
        default_file_path = True

    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_path)
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    # Log fallback warnings using the logger itself
    if default_logger:
        logger.warning("Logger name not provided. Using default: 'bulk_photo_processor'")
    if default_file_path:
        logger.warning("Log file path not provided. Using default: './logs/default.log'")

    return logger