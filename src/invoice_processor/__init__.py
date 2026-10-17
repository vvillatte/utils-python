"""
invoice-processor
Universal PDF Invoice Processing Framework

This module exposes:
- Processor registry
- Base processor class
- Public API for programmatic use
"""

from .processors.base_processor import BaseInvoiceProcessor

# Import processors
from .processors.iinet_internet import IiNetInternetProcessor
from .processors.iinet_mobile import IiNetMobileProcessor
from .processors.chargefox import ChargefoxProcessor
from .processors.qbs import QBSProcessor

# ---------------------------------------------------------------------------
# Processor Registry
# ---------------------------------------------------------------------------

PROCESSOR_REGISTRY = {
    "iinet-internet": IiNetInternetProcessor,
    "iinet-mobile": IiNetMobileProcessor,
    "chargefox": ChargefoxProcessor,
    "qbs": QBSProcessor,
}

def register_processor(name: str, cls: type[BaseInvoiceProcessor]):
    if not issubclass(cls, BaseInvoiceProcessor):
        raise TypeError(f"Processor '{name}' must inherit BaseInvoiceProcessor")
    PROCESSOR_REGISTRY[name] = cls

def get_processor(name: str) -> BaseInvoiceProcessor:
    if name not in PROCESSOR_REGISTRY:
        raise KeyError(
            f"Unknown processor '{name}'. "
            f"Available: {', '.join(PROCESSOR_REGISTRY.keys())}"
        )
    return PROCESSOR_REGISTRY[name]()

def list_processors() -> list[str]:
    return sorted(PROCESSOR_REGISTRY.keys())

__all__ = [
    "register_processor",
    "get_processor",
    "list_processors",
    "BaseInvoiceProcessor",
]
