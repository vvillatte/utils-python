import json
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config(path=None):
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {config_path}: {e}")