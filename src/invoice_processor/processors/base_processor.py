"""
processors.base_processor
-------------------------
Defines the abstract interface for all invoice-type processors.

Each processor must implement:
- extract_fields(text)
- validate(fields)
- build_filename(fields)
- to_json(fields, core_metadata)

This module contains NO invoice-specific logic.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional

from invoice_processor.core.exceptions import (
    FieldExtractionError,
    InvoiceValidationError,
)


class BaseInvoiceProcessor(ABC):
    """
    Abstract base class for all invoice processors.

    Processors must be:
    - Pure (no I/O)
    - Deterministic
    - Stateless
    """

    # ----------------------------------------------------------------------
    # Required Interface
    # ----------------------------------------------------------------------

    @abstractmethod
    def extract_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract invoice-specific fields from raw PDF text.

        Must raise FieldExtractionError on failure.
        """
        raise NotImplementedError

    @abstractmethod
    def validate(self, fields: Dict[str, Any]):
        """
        Validate extracted fields.

        Must raise InvoiceValidationError on failure.
        """
        raise NotImplementedError

    @abstractmethod
    def build_filename(self, fields: Dict[str, Any]) -> str:
        """
        Build the final filename for the invoice PDF.

        Must return a string WITHOUT extension.
        """
        raise NotImplementedError

    @abstractmethod
    def to_json(self, fields: Dict[str, Any], core_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine invoice-specific fields with core metadata.

        Must return a JSON-serializable dictionary.
        """
        raise NotImplementedError

    # ----------------------------------------------------------------------
    # Utility Methods (shared by all processors)
    # ----------------------------------------------------------------------

    def extract_first(self, pattern: str, text: str, flags=0) -> str:
        """
        Extract the first regex match.

        Raises FieldExtractionError if not found.
        """
        match = re.search(pattern, text, flags)
        if not match:
            raise FieldExtractionError(f"Pattern not found: {pattern}")
        return match.group(1).strip()

    def extract_all(self, pattern: str, text: str, flags=0) -> list[str]:
        """
        Extract all regex matches.

        Returns empty list if none found.
        """
        return [m.strip() for m in re.findall(pattern, text, flags)]

    def parse_date(self, raw: str, formats: Optional[list[str]] = None) -> str:
        """
        Parse a date string into ISO 8601 format.

        Raises InvoiceValidationError if parsing fails.
        """
        if formats is None:
            formats = [
                "%d %b %Y",
                "%d %B %Y",
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
            ]

        for fmt in formats:
            try:
                dt = datetime.strptime(raw.strip(), fmt)
                return dt.date().isoformat()
            except ValueError:
                continue

        raise InvoiceValidationError(f"Invalid date format: {raw}")

    def parse_amount(self, raw: str) -> float:
        """
        Parse a monetary amount into a float.

        Raises InvoiceValidationError if parsing fails.
        """
        cleaned = raw.replace("$", "").replace("AUD", "").strip()

        try:
            return float(cleaned)
        except ValueError:
            raise InvoiceValidationError(f"Invalid amount: {raw}")
