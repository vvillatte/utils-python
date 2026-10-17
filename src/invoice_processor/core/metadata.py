"""
core.metadata
----------------
Responsible for computing invariant file-level metadata:

- MD5 checksum
- File size (bytes)
- Last modified timestamp (ISO 8601)
- Page count (provided externally by pdf_reader)

This module contains NO invoice-specific logic.
It is part of the invariant core of the invoice-processor system.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def compute_md5(path: Path, chunk_size: int = 65536) -> str:
    """
    Compute MD5 checksum of a file using secure chunked streaming.

    Parameters
    ----------
    path : Path
        Path to the PDF file.
    chunk_size : int
        Size of chunks to read. Default 64 KB.

    Returns
    -------
    str
        Hexadecimal MD5 checksum.
    """
    md5 = hashlib.md5()

    # Stream file in chunks to avoid loading large PDFs into memory
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5.update(chunk)

    return md5.hexdigest()


def compute_file_size(path: Path) -> int:
    """
    Return file size in bytes.

    Parameters
    ----------
    path : Path

    Returns
    -------
    int
        File size in bytes.
    """
    return path.stat().st_size


def compute_last_modified(path: Path) -> str:
    """
    Return last modified timestamp in ISO 8601 format.

    Parameters
    ----------
    path : Path

    Returns
    -------
    str
        ISO 8601 timestamp.
    """
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def build_core_metadata(path: Path, page_count: int) -> Dict[str, Any]:
    """
    Build the complete core metadata object.

    Parameters
    ----------
    path : Path
        PDF file path.
    page_count : int
        Number of pages extracted by pdf_reader.

    Returns
    -------
    dict
        Core metadata dictionary.
    """
    return {
        "md5": compute_md5(path),
        "size": compute_file_size(path),
        "modified": compute_last_modified(path),
        "pages": page_count,
        "original_filename": path.name,
    }
