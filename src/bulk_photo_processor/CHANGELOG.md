# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Rename-only mode** (`--rename-only` / `-ro`)
  - Allows renaming photos in place without moving them.
- **Move-only mode** (`--move-only` / `-mo`)
  - Allows moving photos into the YYYY/MM structure without renaming.
- **Config-driven mode selection**
  - New `"mode"` field in `config.json` supports:
    - `"full"` (default)
    - `"rename-only"`
    - `"move-only"`
- **Interactive mode now supports operation selection**
  - Users can choose:
    - Rename only
    - Move only
    - Full pipeline
- **Improved CLI architecture**
  - CLI flags override config mode.
  - Config mode applies when no CLI flags are provided.
  - Interactive mode applies when neither CLI nor config mode is used.
- **Pure library modules**
  - `bulk_photo_renamer.py` and `bulk_photo_mover.py` no longer contain CLI logic.
  - All error handling now uses exceptions instead of `print()`.

### Changed
- `process_photos()` now acts purely as a pipeline orchestrator.
- CLI logic consolidated and made consistent across:
  - CLI mode
  - Config mode
  - Interactive mode

### Removed
- Deprecated `main()` functions from renamer and mover modules.
- All direct `print()` error messages in library modules.

