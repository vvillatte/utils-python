import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def _normalize_app_name(app_name: str) -> str:
    """
    Normalize application name depending on OS conventions.
    Windows: PascalCase
    Linux/macOS: lowercase
    """
    if os.name == "nt":
        # Convert to PascalCase (e.g., "save_email_attachments" → "SaveEmailAttachments")
        parts = [p for p in app_name.replace("-", "_").split("_") if p]
        return "".join(part.capitalize() for part in parts)
    else:
        # Linux/macOS: lowercase, hyphens allowed
        return app_name.lower().replace("_", "-")


def _get_default_config_path(app_name: str) -> Path:
    """
    Determine the correct cross-platform config directory for the given application.
    """
    if not app_name or not isinstance(app_name, str):
        raise ValueError("app_name must be a non-empty string")

    normalized = _normalize_app_name(app_name)

    if os.name == "nt":  # Windows
        base = Path(os.getenv("LOCALAPPDATA", Path.home()))
        return base / normalized / "config.json"
    else:  # Linux / macOS
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / normalized / "config.json"


def _ensure_parent_exists(path: Path) -> None:
    """
    Ensure the parent directory exists.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Failed to create configuration directory '{path.parent}': {e}")


def load_config(app_name: str, path: Optional[str | Path] = None) -> Dict[str, Any]:
    """
    Load a JSON configuration file with strong validation and error reporting.
    The caller MUST provide the application name to ensure correct namespacing.
    """
    config_path = Path(path) if path else _get_default_config_path(app_name)

    _ensure_parent_exists(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Create it or specify --config <path>"
        )

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in config file '{config_path}': {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load config file '{config_path}': {e}")

    if not isinstance(data, dict):
        raise RuntimeError(f"Config file must contain a JSON object, got: {type(data)}")

    return data
