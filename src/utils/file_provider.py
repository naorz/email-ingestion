from __future__ import annotations

import re
from pathlib import Path

from src.utils.storage_provider import StorageProvider

DATE_PARTITION_PATTERN = re.compile(r"^timestamp=\d{4}-\d{2}-\d{2}$")


class FileProvider(StorageProvider):
    """Local filesystem implementation of StorageProvider."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def list_namespaces(self) -> list[str]:
        return sorted(
            d.name for d in self.root.iterdir() if d.is_dir() and not d.name.startswith(".")
        )

    def list_date_partitions(self, namespace: str) -> list[str]:
        ns_dir = self.root / namespace
        if not ns_dir.is_dir():
            return []
        return sorted(
            d.name for d in ns_dir.iterdir() if d.is_dir() and DATE_PARTITION_PATTERN.match(d.name)
        )

    def list_files(self, namespace: str, date_partition: str) -> list[dict]:
        partition_dir = self.root / namespace / date_partition
        if not partition_dir.is_dir():
            return []
        results = []
        for f in partition_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                stat = f.stat()
                results.append(
                    {
                        "path": str(f),
                        "filename": f.name,
                        "size_bytes": stat.st_size,
                    }
                )
        return sorted(results, key=lambda x: x["filename"])

    def read_file(self, path: str) -> bytes:
        return Path(path).read_bytes()

    def write_file(self, path: str, content: bytes) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

    def file_exists(self, path: str) -> bool:
        return Path(path).exists()

    def file_stat(self, path: str) -> dict:
        p = Path(path)
        stat = p.stat()
        return {
            "size_bytes": stat.st_size,
            "modified_at": stat.st_mtime,
        }
