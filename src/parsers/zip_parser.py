from __future__ import annotations

import io
import zipfile

from loguru import logger

from src.models import FileFormat, FileType
from src.parsers.base import BaseParser, ParseResult


class ZipParser(BaseParser):
    """Parser for ZIP archive containers."""

    @property
    def format(self) -> FileFormat:
        return FileFormat.ZIP

    @property
    def file_type(self) -> FileType:
        return FileType.CONTAINER

    def can_parse(self, filename: str, content: bytes | None = None) -> bool:
        return filename.lower().endswith(".zip")

    def parse(self, content: bytes, filename: str, lineage: list[str]) -> ParseResult:
        result = ParseResult()

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                # Check for encryption — try reading the first file
                entries = [info for info in zf.infolist() if not info.is_dir()]

                if not entries:
                    logger.warning(f"Empty ZIP archive: {filename}")
                    return result

                for info in entries:
                    try:
                        entry_content = zf.read(info.filename)
                    except RuntimeError as e:
                        if "password" in str(e).lower() or "encrypted" in str(e).lower():
                            result.skipped.append((info.filename, "password_protected"))
                            continue
                        raise

                    entry_lineage = [*lineage, info.filename]
                    result.emails.append((info.filename, entry_content, entry_lineage))

        except zipfile.BadZipFile:
            logger.warning(f"Corrupted ZIP archive: {filename}")
            result.skipped.append((filename, "corrupted"))

        except RuntimeError as e:
            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                logger.warning(f"Password-protected ZIP archive: {filename}")
                result.skipped.append((filename, "password_protected"))
            else:
                raise

        return result
