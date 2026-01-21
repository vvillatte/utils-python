import argparse
from .attachment_downloader import main as run_downloader

def cli():
    parser = argparse.ArgumentParser(
        description="Download attachments from emails based on IMAP search criteria."
    )

    # Optional: allow specifying a config file
    parser.add_argument(
        "--config",
        type=str,
        help="Path to a JSON config file (optional)."
    )

    # Optional: allow overriding the output directory (not used yet)
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Override the download folder defined in the config file."
    )

    parser.add_argument(
        "--mark-read",
        action="store_true",
        help="Mark emails as read after processing."
    )

    parser.add_argument(
        "--archive",
        action="store_true",
        help="Archive emails after downloading attachments."
    )

    # Optional: allow specifying sender (not used yet)
    parser.add_argument(
        "--from",
        dest="from_",
        type=str,
        help="Filter emails by sender address."
    )

    # Optional: allow specifying recipient (not used yet)
    parser.add_argument(
        "--to",
        dest="to",
        type=str,
        help="Filter emails by recipient address."
    )

    parser.add_argument(
        "--subject",
        type=str,
        help="Filter emails by subject substring."
    )

    parser.add_argument(
        "--after",
        type=str,
        help="Filter emails received after YYYY-MM-DD."
    )

    parser.add_argument(
        "--before",
        type=str,
        help="Filter emails received before YYYY-MM-DD."
    )

    parser.add_argument(
        "--unread",
        action="store_true",
        help="Only match unread emails."
    )

    args = parser.parse_args()

    search_overrides = {"from_": args.from_,
                        "to": args.to,
                        "subject": args.subject,
                        "after": args.after,
                        "before": args.before,
                        "unread": args.unread,
    }

    options = {"mark_read": args.mark_read,
               "archive": args.archive,
    }

    run_downloader(
        config_path=args.config,
        output_dir_override=args.output_dir,
        search_overrides=search_overrides,
        options=options,
    )
