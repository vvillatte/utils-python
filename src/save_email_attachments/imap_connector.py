import imaplib
import email
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
        # status, data = server.search(None, *criteria)
        status, data = server.uid("SEARCH", None, *criteria)
        if status != "OK":
            raise Exception(f"UID Search failed: {data}")
        return data[0].split()
    except Exception:
        logger.exception("Error searching emails")
        raise


# ---------------------------------------------------------
# FETCH FULL EMAIL OBJECT
# ---------------------------------------------------------
def fetch_email(server, email_uid):
    try:
        # status, msg_data = server.fetch(email_id, "(RFC822)")
        status, msg_data = server.uid("FETCH", email_uid, "(RFC822)")
        if status != "OK":
            logger.warning(f"Failed to fetch email UID {email_uid}")
            return None
        return email.message_from_bytes(msg_data[0][1])
    except Exception:
        logger.exception(f"Error fetching email UID {email_uid}")
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
# def archive_email(server, email_uid, archive_folder):
#     try:
#         # server.store(email_uid, "+FLAGS", "\\Seen")
#         server.uid("STORE", email_uid, "+FLAGS", "\\Seen")
#         # server.copy(email_id, archive_folder)
#         status, data = server.uid("COPY", email_uid, archive_folder)
#         logger.info(f"UID COPY status={status}, data={data}")
#
#         if status != "OK":
#             logger.error(f"Failed to copy UID {email_uid} to {archive_folder}")
#             return
#
#         server.uid("STORE", email_uid, "+FLAGS", "(\\Deleted)")
#         server.expunge()
#
#         status, data = server.select(archive_folder)
#         logger.info(f"SELECT Archive: status={status}, data={data}")
#         status, data = server.search(None, "ALL")
#         logger.info(f"Archive contains: {data}")
#         server.select("INBOX")
#
#     except Exception:
#         logger.exception(f"Failed to archive email UID {email_uid}")
#         raise
def archive_email(server, email_uid, archive_folder, message_id):
    try:
        # Mark as read
        server.uid("STORE", email_uid, "+FLAGS", "\\Seen")

        # Copy to archive
        status, data = server.uid("COPY", email_uid, archive_folder)
        logger.info(f"UID COPY status={status}, data={data}")

        if status != "OK":
            logger.error(f"Failed to copy UID {email_uid} to {archive_folder}")
            return False

        # --- VERIFICATION STEP ---
        if message_id:
            # Select archive folder
            status, _ = server.select(archive_folder)
            if status != "OK":
                logger.error(f"Cannot select archive folder {archive_folder} for verification")
                return False

            # Search for the copied message by Message-ID
            search_crit = ('HEADER', 'Message-ID', f'"{message_id}"')
            status, data = server.uid("SEARCH", None, *search_crit)
            logger.info(f"Verification search for Message-ID {message_id}: status={status}, data={data}")

            if status != "OK" or not data or not data[0]:
                logger.error(f"Message-ID {message_id} NOT found in archive. Aborting delete.")
                server.select("INBOX")
                return False
        else:
            logger.warning("No Message-ID available for verification")

        # --- DELETE ORIGINAL ONLY IF VERIFIED ---
        server.select("INBOX")
        server.uid("STORE", email_uid, "+FLAGS", "(\\Deleted)")
        server.expunge()
        logger.info(f"Email UID {email_uid} successfully archived")

        return True

    except Exception:
        logger.exception(f"Failed to archive email UID {email_uid}")
        raise

# ---------------------------------------------------------
# CHECK EXISTING FOLDER
# ---------------------------------------------------------
def folder_exists(server, folder_name):
    status, folders = server.list()
    if status != "OK":
        logger.error("Unable to list IMAP folders")
        return False

    available = []
    for f in folders:
        decoded = f.decode()

        # Folder name is always the last whitespace-separated token
        name = decoded.split()[-1].strip('"')

        available.append(name)

    return folder_name in available