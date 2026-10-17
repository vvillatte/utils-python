"""
core.pipeline
----------------
Invariant pipeline for processing a single PDF invoice.

This module coordinates:
- PDF text extraction
- Core metadata computation
- Duplicate detection
- Invoice processor field extraction
- Invoice validation
- Filename generation
- Atomic PDF rename
- Atomic JSON write
- CSV append
- Structured exception handling

This module contains NO invoice-specific logic.
"""

from __future__ import annotations

from pathlib import Path

from logger.logger import setup_logger

from .pdf_reader import extract_pdf_text
from .metadata import build_core_metadata
from .file_ops import (
    safe_filename,
    rename_pdf,
    write_json,
    is_duplicate,
)
from .csv_writer import append_csv_row
from .exceptions import (
    PDFExtractionError,
    InvoiceValidationError,
    FieldExtractionError,
)


# Create a dedicated logger for this module
logger = setup_logger("invoice-processor")


# ---------------------------------------------------------------------------
# Main Pipeline Function
# ---------------------------------------------------------------------------

def process_pdf_file(pdf_path: Path, processor) -> str:
    """
    Process a single PDF invoice using the invariant pipeline.

    Parameters
    ----------
    pdf_path : Path
        Path to the PDF file.
    processor : BaseInvoiceProcessor
        Invoice-type-specific processor instance.

    Returns
    -------
    str
        "OK"       → processed successfully
        "SKIPPED"  → duplicate detected
        "FAILED"   → error occurred (logged)

    Raises
    ------
    PipelineError
        For unrecoverable pipeline-level errors.
    """

    logger.info(f"Starting pipeline for: {pdf_path.name}")

    # ----------------------------------------------------------------------
    # Step 1: PDF Extraction
    # ----------------------------------------------------------------------
    try:
        extraction = extract_pdf_text(pdf_path)
        text = extraction["text"]
        pages = extraction["pages"]
    except PDFExtractionError as ex:
        logger.error(f"PDF extraction failed for {pdf_path.name}: {ex}")
        return "FAILED"

    # ----------------------------------------------------------------------
    # Step 2: Core Metadata
    # ----------------------------------------------------------------------
    try:
        core_meta = build_core_metadata(pdf_path, pages)
    except Exception as ex:
        logger.error(f"Metadata computation failed for {pdf_path.name}: {ex}")
        return "FAILED"

    # ----------------------------------------------------------------------
    # Step 3: Invoice-Specific Field Extraction
    # ----------------------------------------------------------------------
    try:
        fields = processor.extract_fields(text)
    except FieldExtractionError as ex:
        logger.error(f"Field extraction failed for {pdf_path.name}: {ex}")
        return "FAILED"
    except Exception as ex:
        logger.error(f"Unexpected extraction error for {pdf_path.name}: {ex}")
        return "FAILED"

    # ----------------------------------------------------------------------
    # Step 4: Duplicate Detection
    # ----------------------------------------------------------------------
    try:
        invoice_number = fields.get("invoice_number")
        if is_duplicate(pdf_path, core_meta, invoice_number=invoice_number):
            logger.info(f"Duplicate detected, skipping: {pdf_path.name}")
            return "SKIPPED"
    except Exception as ex:
        logger.error(f"Duplicate detection error for {pdf_path.name}: {ex}")
        # Treat duplicate detection failure as non-fatal
        # Continue processing

    # ----------------------------------------------------------------------
    # Step 5: Invoice Validation
    # ----------------------------------------------------------------------
    try:
        processor.validate(fields)
    except InvoiceValidationError as ex:
        logger.error(f"Validation failed for {pdf_path.name}: {ex}")
        return "FAILED"
    except Exception as ex:
        logger.error(f"Unexpected validation error for {pdf_path.name}: {ex}")
        return "FAILED"

    # ----------------------------------------------------------------------
    # Step 6: Filename Generation
    # ----------------------------------------------------------------------
    try:
        final_filename = processor.build_filename(fields)
        final_filename = safe_filename(final_filename)
    except Exception as ex:
        logger.error(f"Filename generation failed for {pdf_path.name}: {ex}")
        return "FAILED"

    # ----------------------------------------------------------------------
    # Step 7: Atomic PDF Rename
    # ----------------------------------------------------------------------
    try:
        new_pdf_path = rename_pdf(pdf_path, final_filename)
    except FileExistsError as ex:
        logger.error(f"Target file already exists: {ex}")
        return "FAILED"
    except Exception as ex:
        logger.error(f"PDF rename failed for {pdf_path.name}: {ex}")
        return "FAILED"

    # ----------------------------------------------------------------------
    # Step 8: JSON Payload Build
    # ----------------------------------------------------------------------
    try:
        json_payload = processor.to_json(fields, core_meta)

        # Add invariant fields
        json_payload.update(
            {
                "final_filename": final_filename,
                "pages": pages,
                "source_file": pdf_path.name,
                "original_filename": core_meta.get("original_filename"),
                "modified": core_meta.get("modified"),
            }
        )
    except Exception as ex:
        logger.error(f"JSON payload build failed for {pdf_path.name}: {ex}")
        return "FAILED"

    # ----------------------------------------------------------------------
    # Step 9: Atomic JSON Write
    # ----------------------------------------------------------------------
    try:
        write_json(new_pdf_path, json_payload)
    except Exception as ex:
        logger.error(f"JSON write failed for {pdf_path.name}: {ex}")
        return "FAILED"

    # ----------------------------------------------------------------------
    # Step 10: CSV Append
    # ----------------------------------------------------------------------
    try:
        append_csv_row(json_payload)
    except Exception as ex:
        logger.error(f"CSV append failed for {pdf_path.name}: {ex}")
        return "FAILED"

    # ----------------------------------------------------------------------
    # Completed Successfully
    # ----------------------------------------------------------------------
    logger.info(f"Pipeline completed successfully for: {final_filename}")
    return "OK"
