from __future__ import annotations

from src.models import FileFormat, FileType
from src.parsers.base import BaseParser, ParseResult


class HtmlParser(BaseParser):
    """Parser for HTML email exports."""

    @property
    def format(self) -> FileFormat:
        return FileFormat.HTML

    @property
    def file_type(self) -> FileType:
        return FileType.SINGLE_EMAIL

    def can_parse(self, filename: str, content: bytes | None = None) -> bool:
        lower = filename.lower()
        return lower.endswith(".html") or lower.endswith(".htm")

    def parse(self, content: bytes, filename: str, lineage: list[str]) -> ParseResult:
        result = ParseResult()
        result.emails.append((filename, content, lineage))
        return result
