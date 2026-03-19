from __future__ import annotations

import mailbox
import re
import tempfile
from pathlib import Path

from loguru import logger

from src.models import FileFormat, FileType
from src.parsers.base import BaseParser, ParseResult


def _sanitize_message_id(message_id: str) -> str:
    """Turn a Message-ID into a safe filename."""
    clean = message_id.strip("<>")
    clean = re.sub(r"[^\w.@-]", "_", clean)
    return clean[:100]  # cap length


class MboxParser(BaseParser):
    """Parser for MBOX mailbox archives."""

    @property
    def format(self) -> FileFormat:
        return FileFormat.MBOX

    @property
    def file_type(self) -> FileType:
        return FileType.CONTAINER

    def can_parse(self, filename: str, content: bytes | None = None) -> bool:
        return filename.lower().endswith(".mbox")

    def parse(self, content: bytes, filename: str, lineage: list[str]) -> ParseResult:
        result = ParseResult()

        # mailbox.mbox needs a file on disk
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mbox") as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            mbox = mailbox.mbox(tmp_path)
            messages = list(mbox)

            if not messages:
                logger.warning(f"Empty MBOX file: {filename}")
                return result

            for idx, message in enumerate(messages):
                msg_id = message.get("Message-ID", "")
                if msg_id:
                    msg_filename = f"{_sanitize_message_id(msg_id)}.eml"
                else:
                    msg_filename = f"msg_{idx:04d}.eml"

                msg_bytes = message.as_bytes()
                entry_lineage = [*lineage, msg_filename]
                result.emails.append((msg_filename, msg_bytes, entry_lineage))

            mbox.close()

        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)

        return result
