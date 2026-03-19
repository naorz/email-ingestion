# Concerns & Deferred Features

## Deferred Formats

### MSG (.msg) — Outlook Message Format

- **Status**: Deferred to P1
- **Package**: [`extract-msg`](https://pypi.org/project/extract-msg/)
- **Why deferred**: Adds a non-trivial dependency tree. The parser interface is fully designed — implementation requires only one new file and one registry entry.
- **Notes**:
  - MSG supports attachments, embedded messages, and rich text (RTF/HTML body)
  - `extract-msg` exposes `.sender`, `.to`, `.subject`, `.body`, and attachment iteration
  - MSG files may contain embedded MSG files (message forwarding) — treat as nested containers

### PST (.pst) — Outlook Personal Storage

- **Status**: Deferred to P1
- **Package**: `pypff` / `libpff` (C bindings)
- **Why deferred**: Requires native C library compilation (platform-specific). Not pip-installable on all systems.
- **Notes**:
  - PST files can be very large (multi-GB) — will need streaming/chunked extraction
  - Consider Docker-based extraction for cross-platform support
  - PST contains a folder hierarchy — need to decide how to flatten into individual emails
  - Alternative: `readpst` CLI tool (from `libpst`) could be called as a subprocess

---

## How to Add a New Parser

The parser system uses a **Strategy/Registry pattern**. Adding a new format requires four steps:

### Step 1: Create the parser file

Create `src/parsers/{format}_parser.py`:

```python
from src.models import FileFormat, FileType
from src.parsers.base import BaseParser, ParseResult

class MyFormatParser(BaseParser):
    @property
    def format(self) -> FileFormat:
        return FileFormat.MY_FORMAT  # Add to FileFormat enum first

    @property
    def file_type(self) -> FileType:
        return FileType.SINGLE_EMAIL  # or FileType.CONTAINER

    def can_parse(self, filename: str, content: bytes | None = None) -> bool:
        return filename.lower().endswith(".myext")

    def parse(self, content: bytes, filename: str, lineage: list[str]) -> ParseResult:
        result = ParseResult()
        # For single email: add to result.emails
        # For container: extract items and add each to result.emails
        # For errors: add to result.skipped
        return result
```

### Step 2: Register in the registry

In `src/parsers/__init__.py`:

```python
from src.parsers.my_format_parser import MyFormatParser

PARSER_REGISTRY[FileFormat.MY_FORMAT] = MyFormatParser()
```

### Step 3: Add format to enum (if new)

In `src/models.py`, add to `FileFormat` and `FORMAT_TYPE_MAP`.

### Step 4: Add tests

In `tests/test_parsers.py`, add test cases for the new parser.

---

## Known Limitations

- **HTML emails**: No inline image extraction — `cid:` URLs are not resolved
- **No retry mechanism**: Transient read failures cause the file to be skipped without retry
- **No MBOX integrity check**: ZIP CRC is verified by `zipfile`, but MBOX has no built-in integrity verification
- **Attachment dedup**: Attachments are stored per-email, not globally deduplicated — same attachment in 100 emails = 100 copies

For performance, concurrency, and operational limitations, see [scaling.md](./scaling.md).
