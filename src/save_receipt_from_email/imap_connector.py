# src/save_receipt_from_email/imap_connector.py

import imaplib
import email
from email.header import decode_header
from .logger import setup_logger

logger = setup_logger()


# ---------------------------------------------------------
# CONNECT TO IMAP
# ---------------------------------------------------------
def connect_imap(config):
    try:
        server = imaplib.IMAP4_SSL(config["host"], config.get("port", 993))
        server.login(config["username"], config["password"])
        server.select(config.get("mailbox", "INBOX"))
        return server
    except Exception:
        logger.exception("Failed to connect to IMAP server")
        raise


# ---------------------------------------------------------
# SEARCH EMAIL IDS
# ---------------------------------------------------------
def search_email_ids(server, criteria):
    try:
        status, data = server.search(None, *criteria)
        if status != "OK":
            raise Exception(f"Search failed: {data}")
        return data[0].split()
    except Exception:
        logger.exception("Error searching emails")
        raise


# ---------------------------------------------------------
# FETCH FULL EMAIL OBJECT
# ---------------------------------------------------------
def fetch_email(server, email_id):
    try:
        status, msg_data = server.fetch(email_id, "(RFC822)")
        if status != "OK":
            logger.warning(f"Failed to fetch email ID {email_id}")
            return None
        return email.message_from_bytes(msg_data[0][1])
    except Exception:
        logger.exception(f"Error fetching email ID {email_id}")
        raise


# ---------------------------------------------------------
# EXTRACT ATTACHMENTS (GENERIC)
# ---------------------------------------------------------
def extract_attachments(msg):
    attachments = []

    for part in msg.walk():
        if part.get_content_disposition() != "attachment":
            continue

        filename = part.get_filename()
        payload = part.get_payload(decode=True)

        if filename and payload:
            attachments.append((filename, payload))

    return attachments


# ---------------------------------------------------------
# ARCHIVE EMAIL
# ---------------------------------------------------------
def archive_email(server, email_id, archive_folder):
    try:
        server.store(email_id, "+FLAGS", "\\Seen")
        server.copy(email_id, archive_folder)
        server.expunge()
    except Exception:
        logger.exception(f"Failed to archive email ID {email_id}")
        raise