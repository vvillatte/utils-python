"""
core.csv_writer
----------------
Responsible for writing invoice records to a master CSV file.

Features:
- Creates CSV with header if missing
- Appends rows safely
- Enforces stable column ordering
- Hardened against partial writes
- Invoice-agnostic (works with any processor)

This module contains NO invoice-specific logic.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, Any


# ---------------------------------------------------------------------------
# CSV Configuration
# ---------------------------------------------------------------------------

# Stable column ordering required by SPEC.md
CSV_COLUMNS = [
    "invoice_type",
    "invoice_number",
    "invoice_date",
    "amount",
    "account_number",
    "service_type",
    "billing_period",
    "customer_name",
    "source_file",
    "final_filename",
    "md5",
    "size",
    "pages",
]

DEFAULT_CSV_NAME = "invoice_records.csv"


# ---------------------------------------------------------------------------
# CSV Writer
# ---------------------------------------------------------------------------

def append_csv_row(record: Dict[str, Any], csv_path: Path | None = None):
    """
    Append a single invoice record to the master CSV file.

    Parameters
    ----------
    record : dict
        Combined core + invoice metadata.
    csv_path : Path, optional
        Custom CSV path. If omitted, DEFAULT_CSV_NAME is used.

    Raises
    ------
    IOError
        If the CSV cannot be written.
    """

    if csv_path is None:
        csv_path = Path(DEFAULT_CSV_NAME)

    # Ensure directory exists
    if csv_path.parent != Path("."):
        csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine if header is needed
    write_header = not csv_path.exists()

    # Prepare row in correct column order
    row = []
    for col in CSV_COLUMNS:
        row.append(record.get(col, ""))

    # Atomic write using temp file
    temp_path = csv_path.with_suffix(".tmp")

    try:
        # If CSV exists, copy existing content into temp file first
        if csv_path.exists():
            with csv_path.open("r", newline="", encoding="utf-8") as src, \
                 temp_path.open("w", newline="", encoding="utf-8") as dst:

                dst.write(src.read())  # copy entire file

        # Append new row
        with temp_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if write_header:
                writer.writerow(CSV_COLUMNS)

            writer.writerow(row)

        # Atomic replace
        temp_path.replace(csv_path)

    except Exception as ex:
        logging.error(f"Failed writing CSV: {csv_path.name} :: {ex}")
        raise IOError(f"Failed writing CSV: {csv_path.name}")
