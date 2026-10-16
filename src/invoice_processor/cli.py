"""
Command-line interface for invoice-processor.

This module:
- Loads the correct processor
- Iterates through PDFs
- Calls the invariant core pipeline
- Handles logging, errors, and summary reporting
"""

import argparse
import sys
from pathlib import Path

from . import get_processor, list_processors
from .core.pipeline import process_pdf_file
from logger.logger import setup_logger

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="invoiceproc",
        description="Universal PDF Invoice Processing Utility"
    )

    parser.add_argument(
        "folder",
        type=str,
        help="Folder containing PDF invoices"
    )

    parser.add_argument(
        "--type",
        required=True,
        choices=list_processors(),
        help="Invoice processor type"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose console output"
    )

    return parser


def main():
    logger = setup_logger("invoice-processor")

    parser = build_parser()
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists() or not folder.is_dir():
        print(f"ERROR: Folder not found: {folder}")
        sys.exit(1)

    processor = get_processor(args.type)

    pdf_files = sorted(folder.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found.")
        sys.exit(0)

    print("=" * 70)
    print(f"Invoice Processor: {args.type}")
    print(f"Input Folder     : {folder.resolve()}")
    print(f"PDF Files Found  : {len(pdf_files)}")
    print("=" * 70)

    processed = 0
    skipped = 0
    failed = 0

    for index, pdf_path in enumerate(pdf_files, start=1):

        if args.verbose:
            print(f"[{index}/{len(pdf_files)}] {pdf_path.name}")

        try:
            result = process_pdf_file(pdf_path, processor)

            if result == "SKIPPED":
                skipped += 1
            elif result == "OK":
                processed += 1
            else:
                failed += 1

        except Exception as ex:
            failed += 1
            logger.error(f"Failed: {pdf_path.name} :: {ex}")
            if args.verbose:
                print(f"  ERROR: {ex}")

    print()
    print("=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Processed : {processed}")
    print(f"Skipped   : {skipped}")
    print(f"Failed    : {failed}")
    print("=" * 70)


if __name__ == "__main__":
    main()
