# 📘 SPEC.MD — Universal PDF Invoice Processing Module

## 1. Purpose and scope

**Goal:** Define an implementation‑agnostic specification for a **universal PDF invoice processing module** that:

- **Separates concerns** between:
  - An **invariant core** (PDF/text/metadata/validation/IO/logging/CSV).
  - A **pluggable invoice processor layer** (invoice‑specific parsing and validation).
- Produces **paired outputs** for each processed invoice:
  - A **PDF file** with a normalized, final filename.
  - A **JSON file** with the **same basename**, in the **same folder**.
- Supports **multiple invoice types** without modifying the core.
- Meets **production‑quality**, **exception‑safe**, and **security‑aware** requirements.

This specification focuses on **functional behavior**, **data model**, **object model**, and **quality requirements**, not on concrete file layout or build tooling.

---

## 2. High‑level architecture

### 2.1 Components

- **Core subsystem (invariant):**
  - **PDF extraction service**
  - **Metadata service**
  - **Duplicate detection service**
  - **Filename normalization and file IO service**
  - **JSON serialization service**
  - **Logging and audit service**
  - **CSV aggregation service**
- **Invoice processor subsystem (variable):**
  - **Base invoice processor interface**
  - **Concrete invoice processors** (iiNet Internet, iiNet Mobile, Chargefox, QBS, etc.)
- **Orchestration / CLI subsystem:**
  - **Command dispatcher**
  - **Folder scanner**
  - **Processing pipeline coordinator**
  - **Summary reporter**

### 2.2 Data flow (conceptual)

1. **Input:** Folder path + invoice type identifier.
2. **Discovery:** Enumerate candidate PDF files.
3. **Core processing per file:**
   - Extract text + page count.
   - Compute file metadata (MD5, size, timestamps).
4. **Invoice processing per file:**
   - Parse invoice‑specific fields from text.
   - Validate invoice‑specific rules.
   - Build final filename.
5. **Duplicate check:** Compare against existing JSON for same final filename.
6. **Output:**
   - Rename/move PDF to final filename.
   - Write JSON with combined core + invoice metadata.
   - Append record to CSV.
   - Log actions and errors.

---

## 3. Data model

### 3.1 Core metadata object

**Name:** `CoreMetadata`

**Fields:**

- **md5:** `string` — MD5 checksum of the PDF file contents.
- **size:** `integer` — File size in bytes.
- **pages:** `integer` — Number of pages in the PDF.
- **modified_timestamp:** `string` (ISO 8601) — Last modified timestamp of the file.
- **original_filename:** `string` — Filename as discovered in the input folder.
- **final_filename:** `string` — Target normalized filename (set after invoice processor runs).

### 3.2 Invoice metadata object

**Name:** `InvoiceMetadata`

**Common fields (for all invoice types):**

- **invoice_type:** `string` — Logical type identifier (e.g., `iinet-internet`).
- **invoice_number:** `string`
- **invoice_date:** `string` (ISO 8601, `YYYY-MM-DD`)
- **amount:** `number` (decimal)
- **account_number:** `string` (optional for some types)
- **service_type:** `string` (e.g., `Internet`, `Mobile`, `Charging`)
- **billing_period:** `string` (human‑readable range)
- **customer_name:** `string`

**Extensibility:**

- Invoice processors may add **type‑specific fields** (e.g., mobile number, charger location) as long as:
  - They are **documented**.
  - They are **serializable** to JSON.
  - They do not conflict with core field names.

### 3.3 JSON output object

**Name:** `InvoiceRecord`

**Definition:** Combination of `CoreMetadata` + `InvoiceMetadata`.

**Example:**

```json
{
  "invoice_type": "iinet-internet",
  "invoice_number": "882230210",
  "invoice_date": "2026-02-07",
  "amount": 30.00,
  "account_number": "1208227551",
  "service_type": "Internet",
  "billing_period": "14 Feb 2026 to 13 Mar 2026",
  "customer_name": "Vincent Villatte",
  "md5": "...",
  "size": 123456,
  "pages": 2,
  "original_filename": "882230210_invoice.pdf",
  "final_filename": "2026-02-07 - AUD 30.00 - iiNet Internet - 882230210.pdf"
}
```

### 3.4 CSV record

**Columns (minimum set):**

- **invoice_type**
- **invoice_number**
- **invoice_date**
- **amount**
- **account_number**
- **service_type**
- **billing_period**
- **customer_name**
- **source_file** (original filename)
- **final_filename**
- **md5**
- **size**
- **pages**

---

## 4. Object model and functional interfaces

### 4.1 PDF extraction service

**Interface name:** `PdfExtractionService`

**Primary function:** `extract_text_and_pages(pdf_path) -> PdfExtractionResult`

**Operations:**

- **Open PDF** in a safe, read‑only mode.
- **Extract text** from all pages.
- **Normalize whitespace** (e.g., collapse multiple spaces, unify line endings).
- **Count pages**.
- **Return:**
  - `text`: full normalized text.
  - `pages`: integer page count.

**Requirements:**

- Must handle:
  - Encrypted or corrupted PDFs by raising well‑defined exceptions.
  - Large PDFs using streaming or incremental reading where possible.
- Must not execute or interpret any embedded scripts or active content in PDFs.

---

### 4.2 Metadata service

**Interface name:** `FileMetadataService`

**Primary function:** `compute_core_metadata(pdf_path) -> CoreMetadata`

**Operations:**

- **Compute MD5 checksum** over the full file contents.
- **Determine file size** in bytes.
- **Read last modified timestamp** from the filesystem.
- **Populate `CoreMetadata`** with:
  - `md5`, `size`, `modified_timestamp`, `original_filename`.

**Requirements:**

- Must be deterministic: same file → same MD5 and size.
- Must handle missing or inaccessible files with clear exceptions.

---

### 4.3 Duplicate detection service

**Interface name:** `DuplicateDetectionService`

**Primary function:**  
`is_duplicate(final_filename, core_metadata, invoice_metadata) -> bool`

**Operations:**

- **Locate JSON file** with the same basename as `final_filename` in the target folder.
- If JSON exists:
  - **Load JSON** safely.
  - Compare:
    - `invoice_number`
    - `md5`
    - `size`
  - If all match → **duplicate**.
- Return `True` if duplicate, `False` otherwise.

**Requirements:**

- Must treat malformed JSON as **non‑fatal**:
  - Log the issue.
  - Treat as **not duplicate** (to avoid silent data loss).
- Must be resilient to partial writes (e.g., truncated JSON).

---

### 4.4 Filename and file IO service

**Interface name:** `FileNamingAndIoService`

**Key functions:**

1. `sanitize_filename(raw_name) -> string`
2. `apply_final_filename(pdf_path, final_filename) -> updated_pdf_path`
3. `write_json_record(target_folder, final_filename, invoice_record) -> json_path`

**Operations:**

- **Sanitize filename:**
  - Remove or replace illegal characters.
  - Enforce a consistent pattern (e.g., no trailing spaces, safe ASCII subset).
- **Rename PDF:**
  - Move/rename the original PDF to the final filename.
  - Ensure atomic or near‑atomic operations where possible.
- **Write JSON:**
  - Create JSON file with the **same basename** as the PDF.
  - Ensure write is:
    - **Atomic** (e.g., write to temp file then rename).
    - **Durable** (flush to disk).

**Requirements:**

- Must never overwrite an existing PDF or JSON without explicit policy:
  - Default: **fail and log** if target exists.
- Must handle filesystem permission errors gracefully.

---

### 4.5 JSON serialization service

**Interface name:** `JsonSerializationService`

**Primary function:** `serialize_invoice_record(invoice_record) -> string`

**Operations:**

- Convert `InvoiceRecord` (core + invoice metadata) into JSON.
- Enforce:
  - **UTF‑8 encoding**
  - **Stable field ordering** (optional but recommended for diffing).
- Validate:
  - All required fields are present.
  - Types are JSON‑compatible.

**Requirements:**

- Must reject non‑serializable values (e.g., complex objects) with clear errors.
- Must avoid leaking internal implementation details (e.g., stack traces) into JSON.

---

### 4.6 Logging and audit service

**Interface name:** `LoggingService`

**Key functions:**

1. `log_info(message, context=None)`
2. `log_warning(message, context=None)`
3. `log_error(message, context=None)`
4. `log_duplicate(file_path, invoice_number, md5)`
5. `log_summary(summary_stats)`

**Operations:**

- Record:
  - Start/end of processing.
  - Per‑file actions (processed, skipped, duplicate, error).
- Maintain:
  - **Audit trail** for later troubleshooting.
- Support:
  - Log rotation or size limits (implementation‑dependent).

**Requirements:**

- Logs must not contain sensitive data beyond what is already present in invoices.
- Must avoid logging secrets (e.g., environment variables, credentials).

---

### 4.7 CSV aggregation service

**Interface name:** `CsvAggregationService`

**Primary function:** `append_record(invoice_record)`

**Operations:**

- Map `InvoiceRecord` fields to CSV columns.
- Append a new row to a **master CSV file**.
- Ensure:
  - **Consistent column ordering**.
  - **Header row** is present and stable.

**Requirements:**

- Must handle concurrent appends safely (implementation‑dependent).
- Must avoid data corruption on partial writes.

---

### 4.8 Base invoice processor interface

**Interface name:** `BaseInvoiceProcessor`

**Key functions:**

1. `extract_fields(text) -> InvoiceMetadata`
2. `validate(fields, core_metadata) -> ValidationResult`
3. `build_final_filename(fields) -> string`
4. `to_invoice_record(fields, core_metadata) -> InvoiceRecord`

**Operations:**

- **extract_fields:**
  - Parse invoice‑specific fields from raw text.
  - Use regex, structured parsing, or other techniques.
- **validate:**
  - Check:
    - Required fields present.
    - Date formats valid.
    - Amounts consistent (e.g., total vs. line items, if applicable).
  - Return:
    - Success/failure.
    - Error messages or codes.
- **build_final_filename:**
  - Construct normalized filename based on fields (e.g., date, amount, type, invoice number).
- **to_invoice_record:**
  - Combine `InvoiceMetadata` with `CoreMetadata` into `InvoiceRecord`.

**Requirements:**

- Must be **pure** with respect to side effects (no IO).
- Must be **deterministic**: same text → same fields.

---

### 4.9 Concrete invoice processors (examples)

**Examples (non‑exhaustive):**

- `IiNetInternetProcessor`
- `IiNetMobileProcessor`
- `ChargefoxProcessor`
- `QbsProcessor`

Each must:

- Implement `BaseInvoiceProcessor`.
- Document:
  - Expected invoice layout.
  - Parsing assumptions.
  - Specific validation rules.

---

### 4.10 Processor registry

**Interface name:** `InvoiceProcessorRegistry`

**Primary function:** `get_processor(invoice_type_identifier) -> BaseInvoiceProcessor`

**Operations:**

- Maintain mapping:
  - `iinet-internet` → `IiNetInternetProcessor`
  - `iinet-mobile` → `IiNetMobileProcessor`
  - `chargefox` → `ChargefoxProcessor`
  - `qbs` → `QbsProcessor`
- Provide:
  - Clear error if unknown type is requested.

**Requirements:**

- Adding a new invoice type must require only:
  - Implementing a new processor.
  - Registering it in the registry.
- No changes to core services.

---

### 4.11 Orchestration / CLI service

**Interface name:** `InvoiceProcessingOrchestrator`

**Primary function:**  
`process_folder(folder_path, invoice_type_identifier) -> ProcessingSummary`

**Operations:**

For each PDF in `folder_path`:

1. **Core phase:**
   - Extract text + pages.
   - Compute core metadata.
2. **Invoice phase:**
   - Use registry to obtain processor.
   - Extract fields.
   - Validate fields.
   - Build final filename.
3. **Duplicate phase:**
   - Check for duplicates.
   - If duplicate:
     - Log and skip.
4. **Output phase:**
   - Rename PDF.
   - Build `InvoiceRecord`.
   - Serialize and write JSON.
   - Append CSV.
5. **Summary phase:**
   - Aggregate counts:
     - Processed
     - Skipped (duplicate)
     - Errors
   - Return `ProcessingSummary`.

**Requirements:**

- Must continue processing on errors (per‑file isolation).
- Must provide clear exit status for CLI (e.g., success with warnings vs. failure).

---

## 5. Functional requirements

- **Multiple invoice types:**  
  Must support different invoice layouts via pluggable processors.

- **Paired outputs:**  
  For each successfully processed invoice:
  - One PDF with final filename.
  - One JSON with same basename in same folder.

- **Duplicate avoidance:**  
  Must detect and skip already processed invoices based on:
  - `invoice_number`
  - `md5`
  - `size`

- **CSV aggregation:**  
  Must maintain a master CSV with one row per processed invoice.

- **Non‑destructive behavior:**  
  Must not overwrite existing files by default.

---

## 6. Performance requirements

- **Batch processing:**  
  Must handle **100+ PDFs** in a single run with acceptable performance.

- **Streaming / memory usage:**
  - Avoid loading extremely large PDFs fully into memory when possible.
  - Use incremental reading strategies where supported.

- **Duplicate short‑circuit:**
  - Duplicate detection should be efficient and avoid unnecessary re‑processing.

---

## 7. Production quality and exception handling

### 7.1 General principles

- **Fail fast per file, not globally:**
  - Errors on one file must not stop the entire batch.
- **Clear error taxonomy:**
  - Distinguish:
    - PDF read errors
    - Parsing errors
    - Validation errors
    - IO errors
    - Duplicate detection errors
- **Structured error reporting:**
  - Each error should have:
    - Type/category
    - Human‑readable message
    - Context (file path, invoice type)

### 7.2 Required behaviors

- **Missing required fields:**
  - Mark file as **failed**.
  - Log error with details.
  - Do not produce JSON/CSV for that file.

- **Invalid date formats / amounts:**
  - Treat as validation failure.
  - Log and skip output.

- **Unreadable PDF:**
  - Log as PDF error.
  - Skip file.

- **Duplicate invoice:**
  - Log as duplicate.
  - Skip re‑processing.

- **Unexpected exceptions:**
  - Catch at orchestration level.
  - Log with minimal stack information (no sensitive data).
  - Continue with next file.

---

## 8. Security and hardening requirements

- **Input validation:**
  - Treat all PDFs and text as **untrusted input**.
  - Do not execute or interpret embedded scripts or active content.
- **Path handling:**
  - Avoid directory traversal vulnerabilities:
    - Sanitize filenames.
    - Restrict operations to intended folders.
- **Resource limits:**
  - Guard against:
    - Extremely large files.
    - Excessive page counts.
  - Implement configurable limits (e.g., max file size, max pages).
- **Logging hygiene:**
  - Avoid logging sensitive data beyond what is necessary for debugging.
  - Do not log environment secrets or credentials.
- **Atomic writes:**
  - Use temp files and renames to avoid partial JSON/CSV corruption.
- **Error messages:**
  - Avoid exposing internal implementation details in user‑visible messages.

---

## 9. Extensibility requirements

- **New invoice types:**
  - Must be addable by:
    - Implementing a new `BaseInvoiceProcessor` subclass.
    - Registering it in `InvoiceProcessorRegistry`.
  - No changes to core services.

- **New output formats (future):**
  - Design should allow:
    - Additional export targets (e.g., database, API) via new services.
    - Without changing existing processors.

---

## 10. Testing requirements

### 10.1 Unit tests

- **PdfExtractionService:**
  - Text extraction and page counting.
- **FileMetadataService:**
  - MD5, size, timestamp correctness.
- **DuplicateDetectionService:**
  - Detection logic with various JSON states.
- **FileNamingAndIoService:**
  - Filename sanitization and safe renaming.
- **BaseInvoiceProcessor implementations:**
  - Field extraction and validation.

### 10.2 Integration tests

- **End‑to‑end folder processing:**
  - Multiple invoice types in one folder.
  - Mixed success, failure, duplicate cases.
- **CSV aggregation:**
  - Correct rows and columns.
- **JSON creation:**
  - Correct structure and field values.

---

## 11. CLI behavior (conceptual)

**Command pattern:**

```text
invoice-processor <input-folder> --type <invoice-type-identifier>
```

**Expected behavior:**

- Validate arguments.
- Resolve processor via registry.
- Run `InvoiceProcessingOrchestrator`.
- Print summary:
  - Number processed
  - Number skipped (duplicates)
  - Number failed (errors)

---

_End of SPEC.MD_