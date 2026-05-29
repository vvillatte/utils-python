import os
import logging
from pathlib import Path
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime
from collections import defaultdict

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
# Helper: ensure unique path
# ---------------------------------------------------------
def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


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
# Extract timestamp from email
# ---------------------------------------------------------
def extract_email_timestamp(msg):
    raw_date = msg.get("Date")
    if not raw_date:
        return None

    try:
        dt = parsedate_to_datetime(raw_date)
        return dt.strftime("%Y%m%d_%H%M%S")
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------
# Save attachment (timestamping controlled externally)
# ---------------------------------------------------------
def save_attachment(filename, payload, output_dir, subject_hint, msg, force_timestamp):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = extract_email_timestamp(msg) or datetime.now().strftime("%Y%m%d_%H%M%S")

    if not filename:
        filename = f"{subject_hint}_{timestamp}"
        filepath = ensure_unique_path(output_dir / filename)
    else:
        p = Path(filename)

        if force_timestamp:
            filename = f"{p.stem}_{timestamp}{p.suffix}"
            filepath = ensure_unique_path(output_dir / filename)
        else:
            filepath = output_dir / filename

    with open(filepath, "wb") as f:
        f.write(payload)

    logging.info(f"Saved attachment: {filepath}")
    return str(filepath)


# ---------------------------------------------------------
# Validate output directory
# ---------------------------------------------------------
def validate_output_dir(path_str):
    if not path_str:
        raise ValueError("Output directory path is empty or None")

    path = Path(path_str).expanduser().resolve()

    if path.exists() and not path.is_dir():
        raise ValueError(f"Output path '{path}' exists but is not a directory")

    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created output directory: {path}")
        except Exception as e:
            raise RuntimeError(f"Failed to create output directory '{path}': {e}")

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
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.handlers.clear()

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


# ---------------------------------------------------------
# Main workflow (two-phase processing)
# ---------------------------------------------------------
def main(config_path=None, output_dir_override=None, search_overrides=None, options=None):
    try:
        config = load_config()
        setup_logging(config['log_file'])
        logging.info("Starting attachment downloader")

        options = options or {}

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

        EXPECTED_SEARCH_FIELDS = ["from_", "to", "subject", "after", "before", "unread"]
        for field in EXPECTED_SEARCH_FIELDS:
            search.setdefault(field, None)

        class ArgsShim:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)

        criteria = build_search_criteria(ArgsShim(search))
        logging.info(f"Final IMAP search criteria list: {criteria}")

        try:
            pretty = " ".join(criteria)
            logging.info(f"IMAP SEARCH command: UID SEARCH {pretty}")
        except TypeError:
            logging.warning("IMAP SEARCH criteria contain non-string elements")

        try:
            validate_search_fields(search)
        except ValueError as e:
            logging.error(f"Invalid search criteria: {e}")
            print(f"Error: {e}")
            return

        email_uids = search_email_ids(server, criteria)
        count = len(email_uids)
        logging.info(f"Matched {count} email{'s' if count != 1 else ''}")

        if not email_uids:
            logging.info("No matching emails found")
            return

        # ---------------------------------------------------------
        # Phase 1: Collect all attachments
        # ---------------------------------------------------------
        all_attachments = []

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
                ts = extract_email_timestamp(msg) or datetime.now().strftime("%Y%m%d_%H%M%S")
                all_attachments.append({
                    "filename": filename,
                    "payload": payload,
                    "msg": msg,
                    "subject": subject,
                    "timestamp": ts,
                    "uid": uid,
                })

        # ---------------------------------------------------------
        # Phase 2: Analyse filename collisions
        # ---------------------------------------------------------
        groups = defaultdict(list)
        for item in all_attachments:
            groups[item["filename"]].append(item)

        for filename, items in groups.items():
            if len(items) == 1:
                items[0]["use_timestamp"] = False
            else:
                for item in items:
                    item["use_timestamp"] = True

        # ---------------------------------------------------------
        # Phase 3: Save attachments
        # ---------------------------------------------------------
        for item in all_attachments:
            save_attachment(
                filename=item["filename"],
                payload=item["payload"],
                output_dir=output_dir,
                subject_hint=item["subject"],
                msg=item["msg"],
                force_timestamp=item["use_timestamp"],
            )

            uid = item["uid"]

            if options.get("mark_read"):
                try:
                    server.uid("STORE", uid, "+FLAGS", "(\\Seen)")
                    logging.info("Marked email as read")
                except Exception as e:
                    logging.error(f"Failed to mark email as read: {e}")

            archive_folder = config["folders"]["archive"]

            if not folder_exists(server, archive_folder):
                logging.error(f"Archive folder '{archive_folder}' does not exist")
                return

            if options.get("archive"):
                logging.info(f"Archiving email to {archive_folder}")
                msg = item["msg"]
                message_id = msg.get("Message-ID")
                archive_email(server, uid, archive_folder, message_id)
                logging.info("Email archived")

        server.logout()
        logging.info("Attachment downloader finished")

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
