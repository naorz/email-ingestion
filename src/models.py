from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class FileFormat(StrEnum):
    EML = "eml"
    HTML = "html"
    MSG = "msg"
    MBOX = "mbox"
    PST = "pst"
    ZIP = "zip"
    UNKNOWN = "unknown"


class FileType(StrEnum):
    SINGLE_EMAIL = "single_email"
    CONTAINER = "container"
    UNKNOWN = "unknown"


FORMAT_TYPE_MAP: dict[FileFormat, FileType] = {
    FileFormat.EML: FileType.SINGLE_EMAIL,
    FileFormat.HTML: FileType.SINGLE_EMAIL,
    FileFormat.MSG: FileType.UNKNOWN,  # Deferred — see concerns.md
    FileFormat.MBOX: FileType.CONTAINER,
    FileFormat.PST: FileType.UNKNOWN,  # Deferred — see concerns.md
    FileFormat.ZIP: FileType.CONTAINER,
    FileFormat.UNKNOWN: FileType.UNKNOWN,
}


class SourceLineage(BaseModel):
    """Traces an email back to its origin — the full breadcrumb trail."""

    namespace: str
    date_partition: str
    source_file: str
    container_path: list[str]  # e.g. ["batch.zip", "inner.mbox"]
    original_filename: str


class DiscoveredFile(BaseModel):
    """A file found during directory scanning (before unpacking)."""

    path: str
    namespace: str
    date_partition: str
    filename: str
    format: FileFormat
    size_bytes: int
    content_hash: str
    discovered_at: datetime


class ProcessedEmail(BaseModel):
    """An individual email file staged for downstream consumption."""

    uid: str
    source_lineage: SourceLineage
    format: FileFormat
    content_hash: str
    output_path: str
    has_attachments: bool
    attachment_dir: str | None = None
    processed_at: datetime


class SkippedFile(BaseModel):
    """Record of a file that was skipped during processing."""

    path: str
    reason: str
    namespace: str
    date_partition: str
    discovered_at: datetime


class PipelineRun(BaseModel):
    """Metadata about a single pipeline execution."""

    run_id: str
    mode: str
    started_at: datetime
    completed_at: datetime | None = None
    files_discovered: int = 0
    files_processed: int = 0
    files_skipped: int = 0
    files_deduplicated: int = 0
