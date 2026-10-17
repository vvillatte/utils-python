"""
core.file_ops
----------------
File operations for the invoice-processor core:

- Safe filename sanitisation
- Duplicate detection (based on JSON metadata)
- Atomic PDF renaming
- Atomic JSON writing
- Hardened filesystem operations

This module contains NO invoice-specific logic.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional


# ---------------------------------------------------------------------------
# Filename Sanitisation
# ---------------------------------------------------------------------------

def safe_filename(name: str) -> str:
    """
    Remove or replace characters that are unsafe for filenames.

    Parameters
    ----------
    name : str

    Returns
    -------
    str
        Sanitised filename.
    """
    unsafe = '<>:"/\\|?*'
    cleaned = name

    for ch in unsafe:
        cleaned = cleaned.replace(ch, "_")

    # Collapse double spaces, trim
    cleaned = " ".join(cleaned.split()).strip()

    return cleaned


# ---------------------------------------------------------------------------
# Duplicate Detection
# ---------------------------------------------------------------------------

def is_duplicate(pdf_path: Path, core_metadata: Dict[str, Any], invoice_number: Optional[str] = None) -> bool:
    """
    Determine whether a PDF has already been processed.

    A file is considered a duplicate if:
    - A JSON file with the same basename exists
    - AND the JSON metadata contains:
        - identical invoice_number (when provided)
        - identical md5
        - identical size

    Parameters
    ----------
    pdf_path : Path
        Path to the PDF file.
    core_metadata : dict
        Metadata computed from the PDF.

    Returns
    -------
    bool
        True if duplicate, False otherwise.
    """

    json_path = pdf_path.with_suffix(".json")

    if not json_path.exists():
        return False

    try:
        with json_path.open("r", encoding="utf-8") as f:
            existing = json.load(f)
    except Exception as ex:
        logging.error(f"Malformed JSON detected: {json_path.name} :: {ex}")
        return False  # Treat malformed JSON as non-duplicate

    # Required fields for duplicate detection
    required = ["md5", "size"]
    if not all(key in existing for key in required):
        return False

    # Fast path: if invoice_number is provided and differs, not a duplicate
    if invoice_number is not None:
        existing_number = existing.get("invoice_number")
        if existing_number is not None and existing_number != invoice_number:
            return False

    # Compare core metadata
    same_md5 = existing["md5"] == core_metadata["md5"]
    same_size = existing["size"] == core_metadata["size"]

    # Only skip if file content matches (md5 + size).
    # invoice_number is used as a fast negative filter when available.
    return same_md5 and same_size


# ---------------------------------------------------------------------------
# Atomic PDF Rename
# ---------------------------------------------------------------------------

def rename_pdf(pdf_path: Path, final_filename: str) -> Path:
    """
    Rename the PDF to its final filename.

    Parameters
    ----------
    pdf_path : Path
    final_filename : str

    Returns
    -------
    Path
        New PDF path.

    Raises
    ------
    FileExistsError
        If the target file already exists.
    """

    target = pdf_path.with_name(final_filename + pdf_path.suffix)

    if target.exists():
        raise FileExistsError(f"Target PDF already exists: {target.name}")

    pdf_path.rename(target)
    return target


# ---------------------------------------------------------------------------
# Atomic JSON Write
# ---------------------------------------------------------------------------

def write_json(pdf_path: Path, payload: Dict[str, Any]):
    """
    Write JSON metadata next to the PDF using atomic write.

    Parameters
    ----------
    pdf_path : Path
        Path to the renamed PDF.
    payload : dict
        JSON metadata.

    Raises
    ------
    IOError
        If the JSON cannot be written.
    """

    json_path = pdf_path.with_suffix(".json")
    temp_path = json_path.with_suffix(".json.tmp")

    try:
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)

        # Atomic replace
        temp_path.replace(json_path)

    except Exception as ex:
        logging.error(f"Failed writing JSON: {json_path.name} :: {ex}")
        raise IOError(f"Failed writing JSON: {json_path.name}")
