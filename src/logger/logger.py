import logging
import os
from pathlib import Path
import platform
from typing import Optional


class LoggerSetupError(Exception):
    """Raised when logger setup fails in a non-recoverable way."""


def _sanitize_app_name(app_name: str) -> str:
    """
    Restrict app_name to a safe subset of characters to avoid
    path traversal or weird filesystem behaviour.
    """
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    sanitized = "".join(c for c in app_name if c in allowed)

    if not sanitized:
        raise ValueError("app_name must contain at least one valid character")

    return sanitized


def get_log_dir(app_name: str) -> Path:
    """
    Returns a per-user log directory for the given app_name.

    Windows:
        %LOCALAPPDATA%/<app_name>/logs/
    Linux/macOS/BSD:
        $XDG_STATE_HOME/<app_name>/logs/
        or ~/.local/state/<app_name>/logs/ if XDG_STATE_HOME is not set.
    """
    app_name = _sanitize_app_name(app_name)
    system = platform.system()

    try:
        if system == "Windows":
            base = os.getenv("LOCALAPPDATA")
            if not base:
                # Fallback to home if LOCALAPPDATA is missing
                base = str(Path.home() / "AppData" / "Local")
            base_path = Path(base)

        else:
            xdg_state = os.getenv("XDG_STATE_HOME")
            if xdg_state:
                base_path = Path(xdg_state)
            else:
                base_path = Path.home() / ".local" / "state"

        return base_path / app_name / "logs"

    except Exception as exc:
        # If something truly unexpected happens, fail fast
        raise LoggerSetupError(f"Failed to determine log directory: {exc}") from exc


def setup_logger(
    app_name: str,
    log_name: Optional[str] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Creates and returns a hardened logger:

    - Writes to a per-user log directory.
    - Adds both file and console handlers.
    - Avoids duplicate handlers.
    - Handles permission errors gracefully.
    - Falls back to console-only logging if file logging fails.

    Parameters:
        app_name: Logical name of the tool (used for directory + logger name).
        log_name: Optional log file name; defaults to "<app_name>.log".
        level:    Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    app_name = _sanitize_app_name(app_name)
    logger = logging.getLogger(app_name)

    # If handlers already exist, just return the logger
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Common formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Always have at least a console handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Try to set up file logging; if it fails, keep console-only
    try:
        log_dir = get_log_dir(app_name)
        log_dir.mkdir(parents=True, exist_ok=True)

        safe_log_name = log_name or f"{app_name}.log"
        # Prevent path traversal in log_name
        safe_log_name = os.path.basename(safe_log_name)

        log_file = log_dir / safe_log_name

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    except (PermissionError, OSError, LoggerSetupError) as exc:
        # Log the issue to console, but do not crash the application
        logger.warning(
            "File logging disabled due to error: %s. "
            "Continuing with console-only logging.",
            exc,
        )

    return logger
