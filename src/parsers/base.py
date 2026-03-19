from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.models import FileFormat, FileType


@dataclass
class ParseResult:
    """Result of parsing a file.

    Attributes:
        emails: List of (filename, content_bytes, lineage_chain) tuples for extracted emails.
        attachments: Map of content_hash → [(attachment_name, attachment_bytes)].
        skipped: List of (path_or_name, reason) tuples for items that couldn't be parsed.
    """

    emails: list[tuple[str, bytes, list[str]]] = field(default_factory=list)
    attachments: dict[str, list[tuple[str, bytes]]] = field(default_factory=dict)
    skipped: list[tuple[str, str]] = field(default_factory=list)


class BaseParser(ABC):
    """Abstract base class for all file format parsers.

    To add a new format:
    1. Create a new file in src/parsers/ (e.g., msg_parser.py)
    2. Subclass BaseParser and implement all abstract members
    3. Register the parser in src/parsers/__init__.py PARSER_REGISTRY
    4. Add the format to FileFormat enum in src/models.py if not already present
    5. Add tests in tests/test_parsers.py
    """

    @property
    @abstractmethod
    def format(self) -> FileFormat:
        """Which file format this parser handles."""
        ...

    @property
    @abstractmethod
    def file_type(self) -> FileType:
        """Whether this handles single emails or containers."""
        ...

    @abstractmethod
    def can_parse(self, filename: str, content: bytes | None = None) -> bool:
        """Check if this parser can handle the given file."""
        ...

    @abstractmethod
    def parse(self, content: bytes, filename: str, lineage: list[str]) -> ParseResult:
        """Parse the file content and return a ParseResult."""
        ...
