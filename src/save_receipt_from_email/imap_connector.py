import imaplib
import email
from email.header import decode_header
from logger import setup_logger

logger = setup_logger()

def connect_imap(config):
    try:
        server = imaplib.IMAP4_SSL(config['host'], config.get('port', 993))
        server.login(config['username'], config['password'])
        server.select(config.get('mailbox', 'INBOX'))
        return server
    except Exception as e:
        logger.exception("Failed to connect to IMAP server")
        raise

def fetch_emails(server, criteria):
    try:
        status, data = server.search(None, *criteria)
        if status != 'OK':
            raise Exception(f"Search failed: {data}")
        email_ids = data[0].split()
        results = []
        for eid in email_ids:
            status, msg_data = server.fetch(eid, '(RFC822)')
            if status != 'OK':
                logger.warning(f"Failed to fetch email ID {eid}")
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            results.append(parse_email(msg))
        return results
    except Exception as e:
        logger.exception("Error fetching emails")
        raise

def parse_email(msg):
    subject, encoding = decode_header(msg.get("Subject"))[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or "utf-8", errors="ignore")
    return {
        "from": msg.get("From"),
        "to": msg.get("To"),
        "subject": subject,
        "date": msg.get("Date"),
        "has_attachments": any(part.get_filename() for part in msg.walk() if part.get_content_disposition() == "attachment"),
        "is_html": any(part.get_content_type() == "text/html" for part in msg.walk()),
        "is_read": "\\Seen" in msg.get("Flags", "")
    }