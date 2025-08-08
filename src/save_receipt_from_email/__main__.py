# src/save_receipt_from_email/__main__.py
from .save_receipt_from_email import main

if __name__ == "__main__":
    main()

# import argparse
# from pathlib import Path
# from config_loader import load_config
# from imap_connector import connect_imap, fetch_emails
# from imap_filters import build_search_criteria
#
# def main():
#     parser = argparse.ArgumentParser(description="IMAP Email Scanner")
#     parser.add_argument("--config", type=str, default=str(Path(__file__).parent / "config.json"))
#     parser.add_argument("--from", dest="from_", help="Sender email")
#     parser.add_argument("--to", help="Recipient email")
#     parser.add_argument("--after", help="Received after YYYY-MM-DD")
#     parser.add_argument("--before", help="Received before YYYY-MM-DD")
#     parser.add_argument("--subject", help="Subject contains")
#     parser.add_argument("--unread", action="store_true", help="Only unread emails")
#     args = parser.parse_args()
#
#     config = load_config(args.config)
#     server = connect_imap(config)
#     criteria = build_search_criteria(args)
#     emails = fetch_emails(server, criteria)
#
#     for email in emails:
#         print(email)
#
# if __name__ == "__main__":
#     main()