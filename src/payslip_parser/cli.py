import argparse
import json
from pathlib import Path

from .parser import parse_payslip


def main():
    parser = argparse.ArgumentParser(
        description="Extract structured data from a payslip PDF."
    )

    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the payslip PDF file"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Optional path to save JSON output"
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    data = parse_payslip(str(pdf_path))

    json_output = json.dumps(data, indent=4)
    print(json_output)

    # Determine output path automatically if not provided
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = pdf_path.with_suffix(".json")

    # Save JSON file
    output_path.write_text(json_output, encoding="utf-8")
    print(f"JSON saved to {output_path}")