from __future__ import annotations

import email
from email.policy import default as default_policy

from loguru import logger

from src.models import FileFormat, FileType
from src.parsers.base import BaseParser, ParseResult
from src.utils.hashing import hash_content


class EmlParser(BaseParser):
    """Parser for RFC 822 .eml email files."""

    @property
    def format(self) -> FileFormat:
        return FileFormat.EML

    @property
    def file_type(self) -> FileType:
        return FileType.SINGLE_EMAIL

    def can_parse(self, filename: str, content: bytes | None = None) -> bool:
        return filename.lower().endswith(".eml")

    def parse(self, content: bytes, filename: str, lineage: list[str]) -> ParseResult:
        result = ParseResult()
        result.emails.append((filename, content, lineage))

        attachments = self._extract_attachments(content)
        if attachments:
            content_hash = hash_content(content)
            result.attachments[content_hash] = attachments

        return result

    def _extract_attachments(self, content: bytes) -> list[tuple[str, bytes]]:
        """Extract non-inline attachments from a MIME email."""
        attachments: list[tuple[str, bytes]] = []
        try:
            msg = email.message_from_bytes(content, policy=default_policy)
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" not in content_disposition:
                    continue
                att_filename = part.get_filename()
                if not att_filename:
                    continue
                payload = part.get_payload(decode=True)
                if payload:
                    attachments.append((att_filename, payload))
        except Exception:
            logger.warning(f"Failed to extract attachments from {content[:50]!r}...")

        return attachments
