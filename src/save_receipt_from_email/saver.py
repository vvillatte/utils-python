import os
from .config import RECEIPT_SAVE_PATH

def save_receipts(receipts: list[dict]) -> None:
    """
    Saves receipts to disk or cloud.
    """
    os.makedirs(RECEIPT_SAVE_PATH, exist_ok=True)
    for i, receipt in enumerate(receipts):
        with open(os.path.join(RECEIPT_SAVE_PATH, f"receipt_{i}.json"), "w") as f:
            f.write(str(receipt))  # Replace with json.dump