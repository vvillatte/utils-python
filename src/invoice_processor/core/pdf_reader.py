"""
Core PDF extraction utilities for invoice-processor.

This module provides:
- Secure PDF loading
- Text extraction from all pages
- Page counting
- Whitespace normalisation
- Hardened exception handling

This module is intentionally invoice-agnostic.
"""

from __future__ import annotations

from logger.logger import setup_logger
from pathlib import Path

import pdfplumber


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be read or parsed."""


def extract_pdf_text(pdf_path: Path) -> dict:
    """
    Extract text and page count from a PDF.

    Parameters
    ----------
    pdf_path : Path
        Path to the PDF file.

    Returns
    -------
    dict
        {
            "text": "<full text>",
            "pages": <int>
        }

    Raises
    ------
    PDFExtractionError
        If the PDF cannot be opened or text cannot be extracted.
    """
    logger = setup_logger("invoice-processor")

    if not pdf_path.exists():
        raise PDFExtractionError(f"File not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise PDFExtractionError(f"Not a PDF file: {pdf_path}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = len(pdf.pages)
            text_parts = []

            for page_index, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text() or ""
                except Exception as ex:
                    logger.error(
                        "Failed extracting text from page %s of %s: %s",
                        page_index + 1,
                        pdf_path.name,
                        str(ex)
                    )
                    page_text = ""

                text_parts.append(page_text)

            full_text = "\n".join(text_parts)

    except Exception as ex:
        raise PDFExtractionError(
            f"Failed to read PDF {pdf_path.name}: {str(ex)}"
        ) from ex

    # Normalise whitespace
    cleaned_text = (
        full_text.replace("\r", "")
                 .replace("\t", " ")
                 .strip()
    )

    if not cleaned_text:
        raise PDFExtractionError(
            f"No extractable text found in PDF: {pdf_path.name}"
        )

    return {
        "text": cleaned_text,
        "pages": pages
    }
