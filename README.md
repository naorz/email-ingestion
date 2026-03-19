# Email File Ingestion Pipeline

A Python pipeline that discovers email files from date-partitioned directories, unpacks containers (ZIP, MBOX), deduplicates globally by content, and stages clean individual email files with full lineage tracing.

## Table of Contents

- [Setup & Run](#setup--run)
- **Documentation**
  - [Design Document](docs/design.md) — architecture, UID strategy, CDC, parser pattern, edge cases, tech choices
  - [Scaling (P1)](docs/scaling.md) — production bottlenecks, solutions, migration path
  - [Concerns & Deferred](docs/concerns.md) — MSG/PST roadmap, parser onboarding guide, known limitations

---

## Setup & Run

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — Python package manager

### Install

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### Run Pipeline

```bash
# Interactive mode (terminal menu)
uv run email-ingest

# Backfill — process everything
uv run email-ingest run --input-dir ./_assignment/test_data --output-dir ./output --mode backfill

# Incremental — only new files
uv run email-ingest run --input-dir ./_assignment/test_data --output-dir ./output --mode incremental

# Check pipeline status
uv run email-ingest status
```

### Run Tests

```bash
uv run pytest           # 70 tests
uv run pytest --cov=src # with coverage
uv run pytest -v        # verbose
```

### Lint & Format

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

---

## Scope

### Implemented (P0)

- EML, HTML, MBOX, ZIP parsing with recursive container unpacking
- Global content-hash deduplication (SHA-256)
- Backfill + incremental CDC with SQLite state persistence
- Attachment extraction for EML files
- Full lineage tracing (namespace → partition → container chain → email)
- Interactive CLI menu + direct CLI commands
- Manifest (`manifest.jsonl`) and skipped file log (`skipped.jsonl`)
- 70 tests covering all 10 assignment edge cases

### Deferred (P1)

- MSG / PST format support — parser interface is ready, see [onboarding guide](docs/concerns.md#how-to-add-a-new-parser)
- Parallel processing, streaming, event-driven CDC — see [scaling analysis](docs/scaling.md)
