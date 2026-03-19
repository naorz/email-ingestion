---
name: Python Best Practices
description: Python-specific coding standards, patterns, and idioms for clean, modern Python code.
---

# Python Best Practices

## 1. Modern Python Standards

- **Python 3.10+**: Use modern syntax — `match` statements, `X | Y` union types, `list[str]` instead of `List[str]`.
- **Type Hints everywhere**: All function signatures must have type hints. Use `typing` module for complex types.
- **Dataclasses / Pydantic**: Use `@dataclass` for simple value objects, `pydantic.BaseModel` for validated data with serialization needs.
- **Pathlib over os.path**: Use `pathlib.Path` for all file system operations. Never use `os.path.join()`.
- **f-strings**: Use f-strings for string formatting. Never use `%` formatting or `.format()`.

## 2. Project Setup

- **pyproject.toml**: Use `pyproject.toml` as the single source for project metadata, dependencies, and tool configuration. No `setup.py` or `setup.cfg`.
- **Virtual environments**: Always use `venv` or equivalent. Document the setup in README.
- **Dependency management**: Pin dependencies in `pyproject.toml`. Use dependency groups for dev/test deps.
- **Linting & Formatting**: Use `ruff` for both linting and formatting (replaces `black`, `isort`, `flake8`).

## 3. Pythonic Patterns

### Use Protocols for Structural Typing

```python
from typing import Protocol

class Readable(Protocol):
    def read(self, size: int = -1) -> bytes: ...

# Any object with a .read() method satisfies this — no inheritance needed
def process(source: Readable) -> bytes:
    return source.read()
```

### Use Enums Properly

```python
from enum import Enum, auto

class FileType(Enum):
    EML = auto()
    HTML = auto()
    MBOX = auto()
    ZIP = auto()
    PST = auto()
    MSG = auto()
    UNKNOWN = auto()
```

### Context Managers for Resources

```python
from contextlib import contextmanager

@contextmanager
def temp_extraction_dir(base: Path):
    tmp = base / f"_extract_{uuid4().hex[:8]}"
    tmp.mkdir(parents=True)
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

### Generator Pipelines for Large Data

```python
def discover_files(root: Path) -> Iterator[Path]:
    """Yield files lazily — don't load everything into memory."""
    for partition_dir in sorted(root.iterdir()):
        if partition_dir.is_dir():
            yield from partition_dir.iterdir()
```

## 4. Error Handling

- **Custom exception hierarchy**: Define a base exception for your project, then specific subclasses.

```python
# core/exceptions.py
class PipelineError(Exception):
    """Base exception for all pipeline errors."""

class FileDiscoveryError(PipelineError):
    """Raised when file discovery fails."""

class ContainerUnpackError(PipelineError):
    """Raised when unpacking a container fails."""

class CorruptedFileError(PipelineError):
    """Raised when a file is corrupted or unreadable."""
```

- **Never bare except**: Always catch specific exception types.
- **Use `raise ... from e`**: Preserve the original exception chain.

```python
try:
    data = parse_email(path)
except ValueError as e:
    raise CorruptedFileError(f"Failed to parse {path}") from e
```

## 5. Performance

- **Generators over lists**: Use generators for processing large datasets. Don't load everything into memory.
- **`collections` module**: Use `defaultdict`, `Counter`, `deque` when appropriate.
- **Avoid premature optimization**: Profile first (`cProfile`, `line_profiler`), then optimize the bottleneck.
- **hashlib for hashing**: Use `hashlib.sha256` for content-based deduplication, never roll your own.

## 6. Imports

- **Absolute imports**: Always use absolute imports from the package root.
- **Import order**: stdlib → third-party → local (enforced by `ruff`).
- **No wildcard imports**: Never use `from module import *`.
- **Import at module level**: Avoid importing inside functions unless there's a circular import to break.

## 7. Configuration

- **Environment variables + defaults**: Use `os.environ.get("KEY", "default")` or a config class.
- **No hardcoded paths**: All paths should be configurable or relative to a known root.
- **Dataclass-based config**:

```python
@dataclass(frozen=True)
class PipelineConfig:
    input_dir: Path
    output_dir: Path
    mode: str = "incremental"  # "incremental" | "backfill"
    max_depth: int = 10
```
