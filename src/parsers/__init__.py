from __future__ import annotations

from src.models import FileFormat
from src.parsers.base import BaseParser, ParseResult
from src.parsers.eml_parser import EmlParser
from src.parsers.html_parser import HtmlParser
from src.parsers.mbox_parser import MboxParser
from src.parsers.zip_parser import ZipParser

# Registry: maps format → parser instance.
# To add a new parser: import it and add an entry here.
PARSER_REGISTRY: dict[FileFormat, BaseParser] = {
    FileFormat.EML: EmlParser(),
    FileFormat.HTML: HtmlParser(),
    FileFormat.ZIP: ZipParser(),
    FileFormat.MBOX: MboxParser(),
}


def get_parser(fmt: FileFormat) -> BaseParser | None:
    """Get the parser for a given format. Returns None if unsupported."""
    return PARSER_REGISTRY.get(fmt)


def is_supported(fmt: FileFormat) -> bool:
    """Check if a format has a registered parser."""
    return fmt in PARSER_REGISTRY


__all__ = [
    "BaseParser",
    "ParseResult",
    "PARSER_REGISTRY",
    "get_parser",
    "is_supported",
]
