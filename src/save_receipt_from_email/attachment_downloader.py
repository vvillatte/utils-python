import os
import logging
from pathlib import Path
from datetime import datetime
from email.header import decode_header

from .config_loader import load_config
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


# 🪵 Setup logging
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
def main():
    try:
        config = load_config()
        setup_logging(config['log_file'])
        logging.info("Starting attachment downloader")

        imap_cfg = {
            "host": config["imap_server"],
            "port": config["imap_port"],
            "username": config["username"],
            "password": config["password"],
            "mailbox": config["folders"]["inbox"],
        }

        logging.info("Connecting to IMAP server...")
        server = connect_imap(imap_cfg)

        # status, folders = server.list()
        # for f in folders:
        #     print(f)

        # Build simple search criteria (extendable later)
        criteria = ["FROM", f'"{config["search"]["sender"]}"']
        logging.info("Searching for target emails...")
        email_uids = search_email_ids(server, criteria)

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
                    output_dir=config["download_folder"],
                    subject_hint=subject,
                )

            archive_folder = config["folders"]["archive"]

            if not folder_exists(server, archive_folder):
                logging.error(f"Archive folder '{archive_folder}' does not exist on the server")
                return

            logging.info(f"Archiving email to {archive_folder}")
            # archive_email(server, eid, archive_folder)
            msg = fetch_email(server, uid)
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
