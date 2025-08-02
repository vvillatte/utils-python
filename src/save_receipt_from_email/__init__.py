"""
save_receipt_from_email

Extracts and saves receipts from email content.
Designed for automation and integration with mailbox workflows.
"""

from .extractor import extract_receipts
from .saver import save_receipts
from .config import RECEIPT_SAVE_PATH, RECEIPT_KEYWORDS

__all__ = [
    "extract_receipts",
    "save_receipts",
    "RECEIPT_SAVE_PATH",
    "RECEIPT_KEYWORDS",
]