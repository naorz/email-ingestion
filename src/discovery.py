from __future__ import annotations

from datetime import UTC, datetime

from loguru import logger

from src.models import DiscoveredFile, FileFormat
from src.utils.hashing import hash_content
from src.utils.state_store import StateStore
from src.utils.storage_provider import StorageProvider

EXTENSION_MAP: dict[str, FileFormat] = {
    ".eml": FileFormat.EML,
    ".html": FileFormat.HTML,
    ".htm": FileFormat.HTML,
    ".msg": FileFormat.MSG,
    ".mbox": FileFormat.MBOX,
    ".pst": FileFormat.PST,
    ".zip": FileFormat.ZIP,
}


def detect_format(filename: str) -> FileFormat:
    """Detect file format from extension (case-insensitive)."""
    lower = filename.lower()
    for ext, fmt in EXTENSION_MAP.items():
        if lower.endswith(ext):
            return fmt
    return FileFormat.UNKNOWN


def discover_files(
    storage: StorageProvider,
    state: StateStore,
    namespace: str,
    date_partition: str,
    mode: str,
) -> list[DiscoveredFile]:
    """Discover files in a single partition.

    In backfill mode: discovers all files.
    In incremental mode: skips files already discovered (same content_hash + path).
    """
    files = storage.list_files(namespace, date_partition)
    discovered: list[DiscoveredFile] = []

    for file_info in files:
        path = file_info["path"]
        filename = file_info["filename"]
        content = storage.read_file(path)
        content_hash = hash_content(content)

        if mode == "incremental" and state.is_source_discovered(content_hash, path):
            logger.debug(f"Skipping already-discovered file: {path}")
            continue

        # Extract the date from partition name (timestamp=YYYY-MM-DD → YYYY-MM-DD)
        date_str = date_partition.replace("timestamp=", "")

        df = DiscoveredFile(
            path=path,
            namespace=namespace,
            date_partition=date_str,
            filename=filename,
            format=detect_format(filename),
            size_bytes=file_info["size_bytes"],
            content_hash=content_hash,
            discovered_at=datetime.now(UTC),
        )

        state.mark_source_discovered(df)
        discovered.append(df)
        logger.info(f"Discovered: {namespace}/{date_partition}/{filename} ({df.format.value})")

    return discovered


def scan_all(
    storage: StorageProvider,
    state: StateStore,
    mode: str,
) -> list[DiscoveredFile]:
    """Scan all namespaces and partitions for files."""
    all_discovered: list[DiscoveredFile] = []

    for namespace in storage.list_namespaces():
        for partition in storage.list_date_partitions(namespace):
            found = discover_files(storage, state, namespace, partition, mode)
            all_discovered.extend(found)

    logger.info(f"Total files discovered: {len(all_discovered)}")
    return all_discovered
