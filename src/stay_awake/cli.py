import argparse
from . import VERSION
from .stay_awake import start_daemon, stop_daemon, daemon_main


def build_parser():
    parser = argparse.ArgumentParser(
        description="Prevent Windows from sleeping using SetThreadExecutionState."
    )

    parser.add_argument(
        "-e", "--enable",
        action="store_true",
        help="Enable stay-awake mode"
    )

    parser.add_argument(
        "-d", "--disable",
        action="store_true",
        help="Disable stay-awake mode"
    )

    parser.add_argument(
        "-t", "--time",
        type=int,
        help="Duration in minutes (only valid with --enable)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit"
    )

    # Hidden internal flag for daemon mode
    parser.add_argument(
        "--_daemon",
        action="store_true",
        help=argparse.SUPPRESS
    )

    return parser


def cli():
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"stay_awake version {VERSION}")
        return

    # Internal daemon entry point
    if args._daemon:
        daemon_main(verbose=args.verbose, minutes=args.time)
        return

    # Validate flags
    if args.enable and args.disable:
        print("Error: cannot enable and disable at the same time")
        return

    if args.enable:
        start_daemon(verbose=args.verbose, minutes=args.time)
        return

    if args.disable:
        stop_daemon()
        return

    parser.print_help()
