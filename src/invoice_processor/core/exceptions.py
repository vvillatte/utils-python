"""
core.exceptions
----------------
Defines the exception hierarchy for the invoice-processor system.

This module contains NO invoice-specific logic.
It provides structured, predictable error types for:

- Core pipeline failures
- PDF extraction failures
- Metadata failures
- Duplicate detection
- Invoice validation
- Processor-level errors
"""


class InvoiceProcessorError(Exception):
    """
    Base class for all invoice-processor errors.
    All custom exceptions inherit from this type.
    """
    pass


# ---------------------------------------------------------------------------
# Core / Pipeline Exceptions
# ---------------------------------------------------------------------------

class PipelineError(InvoiceProcessorError):
    """
    Raised when the invariant pipeline encounters a non-recoverable error.
    """
    pass


class PDFExtractionError(InvoiceProcessorError):
    """
    Raised when a PDF cannot be opened, read, or text cannot be extracted.
    """
    pass


class MetadataError(InvoiceProcessorError):
    """
    Raised when file metadata (MD5, size, timestamps) cannot be computed.
    """
    pass


class DuplicateInvoiceError(InvoiceProcessorError):
    """
    Raised when a file is detected as a duplicate and processing should stop.
    """
    pass


# ---------------------------------------------------------------------------
# Processor Exceptions
# ---------------------------------------------------------------------------

class InvoiceValidationError(InvoiceProcessorError):
    """
    Raised when invoice-specific validation fails:
    - Missing required fields
    - Invalid date formats
    - Invalid amounts
    - Structural inconsistencies
    """
    pass


class FieldExtractionError(InvoiceProcessorError):
    """
    Raised when invoice-specific field extraction fails:
    - Regex mismatch
    - Missing expected text sections
    - Unexpected invoice layout
    """
    pass
