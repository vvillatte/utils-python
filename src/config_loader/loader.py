import json
import os
from pathlib import Path
from typing import Any, Dict


def _get_default_config_path() -> Path:
    """
    Determine the correct cross-platform config directory.
    """
    if os.name == "nt":  # Windows
        base = Path(os.getenv("LOCALAPPDATA", Path.home()))
        return base / "utility-scripts" / "config" / "config.json"
    else:  # Linux / macOS
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / "utility-scripts" / "config.json"


def _ensure_parent_exists(path: Path) -> None:
    """
    Ensure the parent directory exists.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Failed to create configuration directory '{path.parent}': {e}")


def load_config(path: str | Path | None = None) -> Dict[str, Any]:
    """
    Load a JSON configuration file with strong validation and error reporting.
    """
    config_path = Path(path) if path else _get_default_config_path()

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
