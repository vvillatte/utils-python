import os
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
)
from .logger import setup_logger

logger = setup_logger()

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

    logger.info(f"Saved attachment: {filepath}")
    return str(filepath)


# ---------------------------------------------------------
# Main workflow
# ---------------------------------------------------------
def main():
    config = load_config()
    logger.info("Starting attachment downloader")

    imap_cfg = {
        "host": config["imap_server"],
        "port": config["imap_port"],
        "username": config["username"],
        "password": config["password"],
        "mailbox": config["folders"]["inbox"],
    }

    server = connect_imap(imap_cfg)

    # Build simple search criteria (extendable later)
    criteria = ["FROM", f'"{config["search"]["sender"]}"']

    email_ids = search_email_ids(server, criteria)

    if not email_ids:
        logger.info("No matching emails found")
        return

    for eid in email_ids:
        msg = fetch_email(server, eid)
        if not msg:
            continue

        subject = decode_subject(msg.get("Subject"))
        logger.info(f"Processing email: {subject}")

        attachments = extract_attachments(msg)

        if not attachments:
            logger.info("No attachments found in this email")
            continue

        for filename, payload in attachments:
            save_attachment(
                filename=filename,
                payload=payload,
                output_dir=config["download_folder"],
                subject_hint=subject,
            )

        archive_email(server, eid, config["folders"]["archive"])
        logger.info("Email archived")

    server.logout()
    logger.info("Attachment downloader finished")

if __name__ == "__main__":
    main()
