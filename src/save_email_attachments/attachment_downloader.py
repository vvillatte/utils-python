import os
import logging
from pathlib import Path
from datetime import datetime
from email.header import decode_header
from .config_loader import load_config
from .imap_filters import build_search_criteria, validate_search_fields
from .imap_connector import (
    connect_imap,
    search_email_ids,
    fetch_email,
    extract_attachments,
    archive_email,
    folder_exists,
)

# ---------------------------------------------------------
# Helper: decode subject safely
# ---------------------------------------------------------
def decode_subject(raw):
    if not raw:
        return "NoSubject"

    parts = decode_header(raw)
    decoded = ""

    for part, enc in parts:
        if isinstance(part, bytes):
            decoded += part.decode(enc or "utf-8", errors="ignore")
        else:
            decoded += part

    return decoded.replace(" ", "_")


# ---------------------------------------------------------
# Save attachment to disk
# ---------------------------------------------------------
def save_attachment(filename, payload, output_dir, subject_hint):
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{subject_hint}_{timestamp}"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / filename

    with open(filepath, "wb") as f:
        f.write(payload)

    logging.info(f"Saved attachment: {filepath}")
    return str(filepath)

# ---------------------------------------------------------
# Validate the output directory
# ---------------------------------------------------------

def validate_output_dir(path_str):
    if not path_str:
        raise ValueError("Output directory path is empty or None")

    path = Path(path_str).expanduser().resolve()

    # Check if path exists and is a file
    if path.exists() and not path.is_dir():
        raise ValueError(f"Output path '{path}' exists but is not a directory")

    # Create directory if missing
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created output directory: {path}")
        except Exception as e:
            raise RuntimeError(f"Failed to create output directory '{path}': {e}")

    # Check writability
    test_file = path / ".write_test"
    try:
        with open(test_file, "w") as f:
            f.write("ok")
        test_file.unlink()
    except Exception as e:
        raise RuntimeError(f"Output directory '{path}' is not writable: {e}")

    logging.info(f"Validated output directory: {path}")
    return str(path)


# ---------------------------------------------------------
# Setup logging
# ---------------------------------------------------------
def setup_logging(log_path):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    root = logging.getLogger()
    root.handlers.clear()  # remove console handler added by PyCharm or other modules

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

# ---------------------------------------------------------
# Main workflow
# ---------------------------------------------------------
def main(config_path=None, output_dir_override=None, search_overrides=None, options=None):
    try:
        config = load_config()
        setup_logging(config['log_file'])
        logging.info("Starting attachment downloader")

        output_dir = output_dir_override or config["download_folder"]
        output_dir = validate_output_dir(output_dir)
        logging.info(f"Using output directory: {output_dir}")

        search_config = config.get("search", {})
        search = search_config.copy()

        if search_overrides:
            for key, value in search_overrides.items():
                if value is not None:
                    search[key] = value

        logging.info(f"Using search criteria: {search}")

        imap_cfg = {
            "host": config["imap_server"],
            "port": config["imap_port"],
            "username": config["username"],
            "password": config["password"],
            "mailbox": config["folders"]["inbox"],
        }

        logging.info("Connecting to IMAP server...")
        server = connect_imap(imap_cfg)

        # criteria = ["FROM", f'"{config["search"]["sender"]}"']
        EXPECTED_SEARCH_FIELDS = ["from_", "to", "subject", "after", "before", "unread"]

        # Ensure all expected fields exist
        for field in EXPECTED_SEARCH_FIELDS:
            search.setdefault(field, None)

        class ArgsShim:
            """A tiny object to mimic argparse.Namespace for build_search_criteria."""
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)

        criteria = build_search_criteria(ArgsShim(search))
        logging.info(f"Final IMAP search criteria list: {criteria}")

        # Optional: log a human-readable IMAP SEARCH command
        try:
            pretty = " ".join(criteria)
            logging.info(f"IMAP SEARCH command: UID SEARCH {pretty}")
        except TypeError:
            logging.warning("IMAP SEARCH criteria contain non-string elements; cannot format command")

        try:
            validate_search_fields(search)
        except ValueError as e:
            logging.error(f"Invalid search criteria: {e}")
            print(f"Error: {e}")
            return

        email_uids = search_email_ids(server, criteria)
        count = len(email_uids)
        logging.info(f"Matched {count} email{'s' if count != 1 else ''} with given criteria")

        if not email_uids:
            logging.info("No matching emails found")
            return

        for uid in email_uids:
            msg = fetch_email(server, uid)
            if not msg:
                continue

            subject = decode_subject(msg.get("Subject"))
            logging.info(f"Processing email: {subject}")

            attachments = extract_attachments(msg)

            if not attachments:
                logging.info("No attachments found in this email")
                continue

            for filename, payload in attachments:
                save_attachment(
                    filename=filename,
                    payload=payload,
                    output_dir=output_dir,
                    subject_hint=subject,
                )

            if options.get("mark_read"):
                try:
                    server.uid("STORE", uid, "+FLAGS", "(\\Seen)")
                    logging.info("Marked email as read")
                except Exception as e:
                    logging.error(f"Failed to mark email as read: {e}")
            else:
                logging.info("Message not marked as read (per CLI option or default)")

            archive_folder = config["folders"]["archive"]

            if not folder_exists(server, archive_folder):
                logging.error(f"Archive folder '{archive_folder}' does not exist on the server")
                return

            if options.get("archive"):
                logging.info(f"Archiving email to {archive_folder}")
                msg = fetch_email(server, uid)
                message_id = msg.get("Message-ID")
                archive_email(server, uid, archive_folder, message_id)
                logging.info("Email archived")
            else:
                logging.info("Archiving disabled (per CLI option or default)")

        server.logout()
        logging.info("Attachment downloader finished")

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
