# Changelog

All notable changes to this project will be documented in this file.  
This project adheres to the principles of [Keep a Changelog](https://keepachangelog.com/) and uses date‑based versioning.

---

## [Unreleased]

### Added
- CLI flag `--archive` to optionally archive processed emails (archiving is now opt‑in).
- CLI flag `--mark-read` to mark processed emails as read.
- CLI filters: `--to`, `--subject`, `--after`, `--before`, `--unread`.
- Strict validation for:
  - email formats (`from_`, `to`)
  - date formats (`after`, `before`)
  - logical date ranges (`after` ≤ `before`)
  - presence of at least one meaningful search criterion
- Logging of:
  - merged search criteria
  - final IMAP criteria list
  - human‑readable `UID SEARCH` command
  - number of matched emails before processing
- Output directory validation with clear error reporting.
- Safe filename generation for attachments.
- Configurable output directory override via `--output-dir`.

### Changed
- Archiving behaviour inverted: archiving is now disabled by default and must be explicitly enabled with `--archive`.
- Improved error handling for empty or invalid search criteria.
- Cleaner, more modular CLI argument parsing.

### Fixed
- Prevented IMAP `BAD Missing search parameters` errors by validating criteria before connecting.
- Ensured consistent mapping between config keys (`from_`) and CLI arguments.
- Improved exception handling around IMAP command formatting.

---

## [0.1.0] – Initial Release

### Added
- Basic IMAP connection and email fetching.
- Sender‑based filtering.
- Attachment extraction and saving.
- Automatic archiving of processed emails.
- Basic logging.