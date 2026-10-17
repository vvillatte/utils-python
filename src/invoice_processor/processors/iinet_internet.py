"""
processors.iinet_internet
-------------------------
Invoice processor for iiNet Internet invoices.

Responsibilities:
- Extract invoice-specific fields from PDF text
- Validate extracted fields
- Build final filename
- Produce JSON metadata

This processor is PURE (no I/O) and deterministic.
"""

from __future__ import annotations

import re
from typing import Dict, Any

from invoice_processor.processors.base_processor import BaseInvoiceProcessor
from invoice_processor.core.exceptions import (
    FieldExtractionError,
    InvoiceValidationError,
)


class IiNetInternetProcessor(BaseInvoiceProcessor):
    """
    Processor for iiNet Internet invoices.

    Expected fields:
    - invoice_number
    - invoice_date
    - account_number
    - amount
    - billing_period
    - customer_name
    - service_type = "Internet"
    """

    SERVICE_TYPE = "Internet"
    INVOICE_TYPE = "iinet-internet"

    # ----------------------------------------------------------------------
    # Field Extraction
    # ----------------------------------------------------------------------

    def extract_fields(self, text: str) -> Dict[str, Any]:
        fields = {}

        # Invoice Number
        fields["invoice_number"] = self.extract_first(
            r"Invoice\s*Number[:\s]+(\S+)", text, flags=re.IGNORECASE
        )

        # Invoice Date
        raw_date = self.extract_first(
            r"Invoice\s*Date[:\s]+([A-Za-z0-9/ ]+)", text, flags=re.IGNORECASE
        )
        fields["invoice_date"] = self.parse_date(raw_date)

        # Account Number
        fields["account_number"] = self.extract_first(
            r"Account\s*Number[:\s]+(\S+)", text, flags=re.IGNORECASE
        )

        # Customer Name
        fields["customer_name"] = self.extract_first(
            r"ATTN:[:\s]+(.+?)(?=\s+(Billing|Invoice|Account)\b)", text, flags=re.IGNORECASE
        )

        # Billing Period
        fields["billing_period"] = self.extract_first(
            r"Billing\s*Period[:\s]+(.+)", text, flags=re.IGNORECASE
        )

        # Amount Due
        raw_amount = self.extract_first(
            r"Internet\s*Total[:\s]+\$?([0-9.,]+)", text, flags=re.IGNORECASE
        )
        fields["amount"] = self.parse_amount(raw_amount)

        # Service Type
        fields["service_type"] = self.SERVICE_TYPE

        # Invoice Type
        fields["invoice_type"] = self.INVOICE_TYPE

        return fields

    # ----------------------------------------------------------------------
    # Validation
    # ----------------------------------------------------------------------

    def validate(self, fields: Dict[str, Any]):
        required = [
            "invoice_number",
            "invoice_date",
            "account_number",
            "customer_name",
            "billing_period",
            "amount",
            "service_type",
            "invoice_type",
        ]

        missing = [key for key in required if key not in fields]
        if missing:
            raise InvoiceValidationError(
                f"Missing required fields: {', '.join(missing)}"
            )

        if fields["amount"] <= 0:
            raise InvoiceValidationError("Amount must be positive")

    # ----------------------------------------------------------------------
    # Filename Generation
    # ----------------------------------------------------------------------

    def build_filename(self, fields: Dict[str, Any]) -> str:
        """
        Format:
        YYYY-MM-DD - AUD <amount> - iiNet Internet - <invoice_number>
        """
        return (
            f"{fields['invoice_date']} - AUD {fields['amount']:.2f} - "
            f"iiNet Internet - {fields['invoice_number']}"
        )

    # ----------------------------------------------------------------------
    # JSON Mapping
    # ----------------------------------------------------------------------

    def to_json(self, fields: Dict[str, Any], core_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine invoice-specific fields with core metadata.
        """
        json_data = {}

        # Invoice-specific fields
        json_data.update(fields)

        # Core metadata
        json_data.update(core_metadata)

        return json_data
