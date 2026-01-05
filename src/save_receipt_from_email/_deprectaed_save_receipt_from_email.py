import imaplib
import email
import os
import re
import requests
import logging
from html import unescape
from datetime import datetime
from email.header import decode_header
from .config_loader import load_config

# 🔌 Connect to IMAP
def connect_imap(config):
    conn = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
    conn.login(config['username'], config['password'])
    return conn

# List emails
def list_emails(conn, config):
    conn.select(config['folders']['inbox'])
    status, messages = conn.search(None, "ALL")
    if status != "OK":
        print("Failed to retrieve emails.")
        return

    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} emails.\n")

    for i, email_id in enumerate(email_ids, 1):
        status, msg_data = conn.fetch(email_id, "(RFC822)")
        if status != "OK":
            print(f"Failed to fetch email ID {email_id.decode()}")
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="replace")
        print(f"{i}. {subject}")

# 🔍 Search for target emails
def search_emails(conn, config):
    conn.select(config['folders']['inbox'])

    criteria = f'(FROM "{config["search"]["sender"]}")'
    logging.info(f"IMAP search criteria: {criteria}")

    status, data = conn.search(None, criteria)
    if status != "OK":
        logging.error("IMAP search failed.")
        return []

    email_ids = data[0].split()
    logging.info(f"Search returned {len(email_ids)} email(s).")

    for email_id in email_ids:
        status, msg_data = conn.fetch(email_id, "(RFC822)")
        if status != "OK":
            logging.warning(f"Failed to fetch email ID {email_id.decode()}")
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        sender_raw = msg.get("From", "")
        sender_parts = decode_header(sender_raw)
        sender = ""
        for part, enc in sender_parts:
            if isinstance(part, bytes):
                sender += part.decode(enc or "utf-8", errors="replace")
            else:
                sender += part

        logging.info(f"Matched email ID {email_id.decode()} from: {sender}")

    return email_ids

# 🔗 Extract PDF URL from email
def parse_url(msg):
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", "")).lower()

            if "attachment" in content_disposition:
                continue

            if content_type in ["text/plain", "text/html"]:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        decoded = payload.decode(charset, errors="ignore")
                    except Exception:
                        decoded = payload.decode("utf-8", errors="ignore")
                    body += decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="ignore")

    # Unescape HTML entities
    body = unescape(body)

    # Extract href URL pointing to a PDF
    match = re.search(
        r'href=["\'](https://agent\.propertytree\.com/external/api/attachments\?c=[^"\']+&f=[^"\']+\.pdf)["\']',
        body,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None

# 📥 Download PDF
def download_pdf(url, config, filename_hint):
    try:
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()

        # Try to extract filename from final URL
        final_url = response.url
        logging.info(f"final url: {final_url}")

        match = re.search(r'/([^/]+\.pdf)(\?|$)', final_url)
        if match:
            filename = match.group(1)
        else:
            # Fallback to timestamped name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{filename_hint}_{timestamp}.pdf"

        output_dir = "data/receipts"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "wb") as f:
            f.write(response.content)

        filepath = os.path.join(config['download_folder'], filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)

        return filepath

    except Exception as e:
        logging.error(f"Failed to download PDF: {e}")
        raise

# 📦 Archive email
def archive_email(conn, email_id, config):
    conn.store(email_id, '+FLAGS', '\\Seen')
    conn.copy(email_id, config['folders']['archive'])
    # conn.store(email_id, '+FLAGS', '\\Deleted')
    conn.expunge()

# 🪵 Setup logging
def setup_logging(log_path):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

# 🚀 Main workflow
def main():
    try:
        config = load_config()
        setup_logging(config['log_file'])

        logging.info("Connecting to IMAP server...")
        conn = connect_imap(config)

        # logging.info("List all emails...")
        # list_emails(conn, config)

        logging.info("Searching for target emails...")
        email_ids = search_emails(conn, config)

        if not email_ids:
            logging.info("No matching emails found.")
            return

        for email_id in email_ids:
            status, data = conn.fetch(email_id, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            subject = msg.get('Subject', 'NoSubject').replace(' ', '_')

            logging.info(f"Processing email: {subject}")
            url = parse_url(msg)

            if not url:
                logging.warning("No valid PDF URL found in email.")
                continue

            try:
                logging.info(f"Downloading PDF from: {url}")
                filepath = download_pdf(url, config, subject)
                logging.info(f"Downloaded PDF to: {filepath}")
                archive_email(conn, email_id, config)
                logging.info("Email archived successfully.")
            except Exception as e:
                logging.error(f"Error downloading or archiving email: {e}")

        conn.logout()

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
