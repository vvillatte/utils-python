from __future__ import annotations

import argparse
from typing import Optional


def cmd_write(url: str) -> None:
    """
    Write a URL to an NFC tag.

    TODO: implement NFC logic using pyscard + ACR1252U.
    """
    print(f"[nfc-tool] (stub) Would write URL to tag: {url}")


def cmd_read() -> None:
    """
    Read data from an NFC tag.

    TODO: implement NFC logic to read NDEF / raw data.
    """
    print("[nfc-tool] (stub) Would read data from tag.")


def cmd_info() -> None:
    """
    Show information about the NFC tag/reader.

    TODO: implement NFC logic to show tag type, UID, tech, etc.
    """
    print("[nfc-tool] (stub) Would show tag/reader info.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nfc-tool",
        description="Helper CLI for writing and inspecting NFC tags.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # write
    write_parser = subparsers.add_parser(
        "write",
        help="Write a URL to an NFC tag.",
    )
    write_parser.add_argument(
        "url",
        help="The URL to write to the NFC tag.",
    )

    # read
    subparsers.add_parser(
        "read",
        help="Read data from an NFC tag.",
    )

    # info
    subparsers.add_parser(
        "info",
        help="Show information about the NFC tag/reader.",
    )

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "write":
        cmd_write(args.url)
    elif args.command == "read":
        cmd_read()
    elif args.command == "info":
        cmd_info()
    else:
        parser.error(f"Unknown command: {args.command!r}")