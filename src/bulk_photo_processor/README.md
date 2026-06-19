# Bulk Photo Processor

A flexible, modular tool for renaming and organising photos into a clean
`YYYY/MM` folder structure. Supports CLI mode, config mode, and interactive mode.

## Features

- Rename photos from `YYYYMMDD_HHMMSS.ext` to  
  `YYYY-MM-DDTHH_MM_SS-000001.ext`
- Move photos into `YYYY/MM` folders
- Detect and skip duplicates using file size + checksum
- Test mode (dry-run)
- Verbose mode
- Three execution modes:
  - **CLI mode**
  - **Config mode**
  - **Interactive mode**
- Three operation modes:
  - **Rename only**
  - **Move only**
  - **Full pipeline (rename + move)**

---

## Installation

```bash
poetry install
```

---

# ## 📘 Usage

### ### **CLI Mode (strict)**  
Provide both source and destination:

```bash
bulk-photo -s <source> -d <destination>
```

### **Test mode**

```bash
bulk-photo -s src -d dst --test
```

### **Verbose mode**

```bash
bulk-photo -s src -d dst --verbose
```

---

## 🛠 Operation Modes

### **Rename only**

```bash
bulk-photo -s src -d dst --rename-only
```

or short:

```bash
bulk-photo -s src -d dst -ro
```

### **Move only**

```bash
bulk-photo -s src -d dst --move-only
```

or short:

```bash
bulk-photo -s src -d dst -mo
```

### **Full pipeline (default)**

```bash
bulk-photo -s src -d dst
```

---

## 📁 Config Mode

If you provide a config file:

```bash
bulk-photo -c config.json
```

Or use the default:

```bash
bulk-photo -c default
```

### **Example `config.json`**

```json
{
  "folders": {
    "source": "D:/tmp/Dump/import/DCIM/Camera",
    "target": "D:/tmp/Album"
  },
  "logger_name": "bulk_photo_processor",
  "log_file": "./logs/bulk_photo_processor.log",
  "flags": {
    "test": false,
    "verbose": true
  },
  "mode": "full"
}
```

### **Supported modes**

- `"full"` — rename then move (default)  
- `"rename-only"`  
- `"move-only"`

### **Precedence**

1. **CLI flags override everything**  
2. Config `"mode"` applies when no CLI flags  
3. Default is `"full"`

---

## 🧭 Interactive Mode

If no CLI parameters and no config file are provided, the tool enters interactive mode.

You will be prompted for:

- Source folder  
- Destination folder  
- Test mode  
- Verbose mode  
- **Operation mode**  
  - Rename only  
  - Move only  
  - Full pipeline  

---

## 🧩 Library Usage

You can also call the modules directly:

```python
from bulk_photo_processor import process_photos
from bulk_photo_renamer import rename_photos
from bulk_photo_mover import move_photos
```

---

## 📝 Logging

Logs are written to the file specified in:

```json
"log_file": "./logs/bulk_photo_processor.log"
```

---
## 📂 Project Structure
```text
bulk_photo_processor/
│
├── cli.py                 # CLI entry point
├── bulk_photo_processor.py # Orchestrates rename + move
├── bulk_photo_renamer.py   # Pure renamer module
├── bulk_photo_mover.py     # Pure mover module
├── config_loader.py        # Loads and validates config files
├── logger.py               # Logging setup
└── ...
```

---

## 🧪 Testing
You can safely test without modifying any files:

```bash
bulk-photo -s src -d dst --test
```

---

## 📄 License

GPL-3.0-or-later