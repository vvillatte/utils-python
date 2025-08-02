import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

RECEIPT_SAVE_PATH = config.get("receipt_save_path", "data/receipts")
RECEIPT_KEYWORDS = config.get("receipt_keywords", [])
FILE_FORMAT = config.get("file_format", "json")
MAX_RECEIPTS_PER_EMAIL = config.get("max_receipts_per_email", 10)