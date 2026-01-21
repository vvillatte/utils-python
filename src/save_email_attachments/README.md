# 📬 IMAP Scanner & attachment downloader

A modular, configurable IMAP email scanning toolkit built for automation, filtering, and robust attachment processing. Designed for clarity, safety, and long‑term maintainability.

---

## 🚀 Features

### Core IMAP Scanner
- 🔧 Configurable IMAP connection via `config.json` 
- 🔍 Flexible search filters: sender, recipient, subject, date ranges, unread‑only 
- 🧩 Modular architecture (config loader, connector, filters, logging)
- 📝 Clean, timestamped logs for every run

### Attachment Downloader
- 📎 Extracts all attachments from matching emails
- 📁 Saves files to a configurable or CLI‑overridden output directory
- 🗂️ Optional archiving of processed emails (--archive)
- 👁️ Optional marking of emails as read (--mark-read)
- 🛡️ Strict validation of search criteria (email format, date format, logical consistency)
- 🔍 Logs the exact IMAP UID SEARCH command for full transparency
- 🧱 Designed for cron‑safe, unattended operation

---

## 📦 Project Structure

```
save_email_attachments/
├── attachment_downloader.py # Main processing pipeline (does the heavy lifting)
├── cli.py                   # CLI entry point
├── config.json              # Default configuration
├── config_loader.py         # Loads config from file
├── imap_connector.py        # Connects to IMAP and fetches emails
├── imap_filters.py          # Builds IMAP search criteria
├── logger.py                # Sets up logging
├── __main__.py              # CLI entry point
├── __init__.py              # Package initializer
└── logs/
    └── attachments_downloader.log          # Log output
```

---

## ⚙️ Configuration

Create or edit `config.json` in the root directory. It defines IMAP credentials, folders, and defaults:

```json
{
  "imap_server": "imap.example.com",
  "imap_port": 993,
  "username": "your@email.com",
  "password": "yourpassword",
  "download_folder": "./data/attachments",
  "folders": {
    "inbox": "INBOX",
    "archive": "INBOX.Archive"
  },
  "search": {
    "from_": "sender@example.com"
  },
  "log_file": "./logs/attachment_downloader.log"
}
```

If no --config is provided, the default path is used. This defaults to `./config.json`.

---

## 🧪 Usage

Run the attachment downloader:

```bash
poetry run save-email-attachments [options]
```
or, if installed as a module:
```bash
python -m save_email_attachments [options]
```

### 🔍 Available Options

| Option             | Description                                    |
|--------------------|------------------------------------------------|
| `--config` PATH    | Path to config file (default: `./config.json`) |
| `--output-dir` DIR | Override download folder                       |
| `--from`           | Filter by sender                               |
| `--to`             | Filter by recipient                            |
| `--subject`        | Filter by subject                              |
| `--after`          | Received after date (`YYYY-MM-DD`)             |
| `--before`         | Received before date (`YYYY-MM-DD`)            |
| `--unread`         | Only unread emails                             |
| `--unread`         | Only match unread emails                       |
| `--archive`        | Archive processed emails (opt-in)              |
| `--mark-read`      | Mark processed emails as read (opt-in)         |

All filters are merged with config defaults and validated before IMAP is contacted.

### 🧾 Example

Download unread invoices from a sender:
```bash
poetry run save-email-attachments --from invoices@example.com --unread
```

Download emails from a date range:
```bash
poetry run save-email-attachments --after 2026-01-01 --before 2026-01-16
```

Save attachments to a custom folder:
```bash
poetry run save-email-attachments --output-dir D:/tmp/invoices
```

Process and archive:
```bash
poetry run save-email-attachments --archive
```

Mark emails as read:
```bash
poetry run save-email-attachments --mark-read
```
---
## 🛡️ Validation

Before any IMAP connection is made, the tool validates:

- Email formats (from_, to)
- Date formats (after, before)
- Logical consistency (after ≤ before)
- At least one meaningful search criterion
- Output directory existence and permissions

Invalid input stops execution early with a clear error message.

---
## 📎 Attachment Processing
For each matching email:

1. Subject is decoded safely
2. All attachments are extracted
3. Files are saved with collision‑safe filenames
4. Optional: email is marked as read
5. Optional: email is archived

All actions are logged
---

## 🛠️ Extending

The system is intentionally modular:

- Add new search filters → imap_filters.py
- Add new validation rules → validation.py
- Add new IMAP operations → imap_connector.py
- Add new CLI flags → cli.py

Everything is structured for clarity and future growth.

---

## 🧪 Testing

Planned test coverage:

- Config loading ✔️
- Search criteria validation ️✔️
- IMAP search builder ✔️
- Attachment extraction ✔️
- Filename sanitisation ❌ __TODO__
- End‑to‑end dry‑run mode ❌ __TODO__

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first to discuss what you’d like to change.

---

## ✨ Author

Crafted by Vincent Villatte — pragmatic innovator, automation enthusiast, and steward of elegant solutions.