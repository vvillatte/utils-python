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


def _normalize_app_name(app_name: str) -> str:
    """
    Normalize application name depending on OS conventions.
    Windows: PascalCase
    Linux/macOS: lowercase with hyphens
    """
    sanitized = _sanitize_app_name(app_name)

    if os.name == "nt":
        # Convert to PascalCase
        parts = sanitized.replace("-", "_").split("_")
        return "".join(p.capitalize() for p in parts if p)
    else:
        # Linux/macOS: lowercase, hyphens allowed
        return sanitized.lower().replace("_", "-")


def get_log_dir(app_name: str) -> Path:
    """
    Returns a per-user log directory for the given app_name.

    Windows:
        %LOCALAPPDATA%/<AppName>/logs/
    Linux/macOS/BSD:
        $XDG_STATE_HOME/<app-name>/logs/
        or ~/.local/state/<app-name>/logs/ if XDG_STATE_HOME is not set.
    """
    normalized = _normalize_app_name(app_name)
    system = platform.system()

    try:
        if system == "Windows":
            base = os.getenv("LOCALAPPDATA")
            if not base:
                base = str(Path.home() / "AppData" / "Local")
            base_path = Path(base)
        else:
            xdg_state = os.getenv("XDG_STATE_HOME")
            base_path = Path(xdg_state) if xdg_state else Path.home() / ".local" / "state"

        return base_path / normalized / "logs"

    except Exception as exc:
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
    """
    normalized = _normalize_app_name(app_name)
    logger = logging.getLogger(normalized)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File handler
    try:
        log_dir = get_log_dir(app_name)
        log_dir.mkdir(parents=True, exist_ok=True)

        safe_log_name = os.path.basename(log_name or f"{normalized}.log")
        log_file = log_dir / safe_log_name

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    except (PermissionError, OSError, LoggerSetupError) as exc:
        logger.warning(
            "File logging disabled due to error: %s. Continuing with console-only logging.",
            exc,
        )

    return logger
