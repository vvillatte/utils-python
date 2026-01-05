# 📬 IMAP Scanner

A modular, configurable IMAP email scanner built for automation, filtering, and logging. Designed with clarity and scalability in mind.

---

## 🚀 Features

- 🔧 Configurable IMAP connection via `config.json`
- 🔍 Flexible email filtering (sender, subject, date, unread, etc.)
- 📁 Modular design: separate config, logging, filters, and connector
- 📜 CLI interface for quick scanning
- 📂 Logs stored automatically in `logs/scanner.log`

---

## 📦 Project Structure

```
imap_scanner/
├── config.json              # Default configuration
├── config_loader.py         # Loads config from file
├── logger.py                # Sets up logging
├── imap_connector.py        # Connects to IMAP and fetches emails
├── imap_filters.py          # Builds IMAP search criteria
├── __main__.py              # CLI entry point
├── __init__.py              # Package initializer
└── logs/
    └── scanner.log          # Log output
```

---

## ⚙️ Configuration

Create or edit `config.json` in the root directory:

```json
{
  "host": "imap.example.com",
  "port": 993,
  "username": "your@email.com",
  "password": "yourpassword",
  "mailbox": "INBOX"
}
```

If no path is provided, the scanner defaults to `./config.json`.

---

## 🧪 Usage

Run from the command line:

```bash
python -m imap_scanner [options]
```

### 🔍 Available Options

| Option         | Description                          |
|----------------|--------------------------------------|
| `--config`     | Path to config file (default: `./config.json`) |
| `--from`       | Filter by sender email               |
| `--to`         | Filter by recipient email            |
| `--subject`    | Filter by subject content            |
| `--after`      | Received after date (`YYYY-MM-DD`)   |
| `--before`     | Received before date (`YYYY-MM-DD`)  |
| `--unread`     | Only unread emails                   |

### 🧾 Example

```bash
python -m imap_scanner --from boss@example.com --unread --after 2025-08-01
```

---

# 📎 Attachment Downloader

A new module, `attachment_downloader.py`, provides a generic and extensible way to download **any** attachments from emails.

## Features

- Connects to IMAP using the existing configuration system
- Searches emails using flexible criteria (currently sender-based)
- Extracts all attachments from matching emails
- Saves them to a configured folder
- Archives processed emails
- Fully modular and easy to extend

## Usage

Run the downloader:

```bash
python -m save_receipt_from_email.attachment_downloader
```

---

## 🛠️ Extending

Want to add filters for attachments, HTML content, or flags? Modify `imap_filters.py` and `imap_connector.py` — the modular design makes it easy.

---

## 🧪 Testing

Coming soon: unit tests for config loading, filter parsing, and email parsing.

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first to discuss what you’d like to change.

---

## ✨ Author

Crafted by Vincent — pragmatic innovator, automation enthusiast, and steward of elegant solutions.