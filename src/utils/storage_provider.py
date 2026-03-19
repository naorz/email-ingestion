from __future__ import annotations

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Abstract interface for storage operations.

    Allows swapping local filesystem for S3/GCS/Azure Blob by implementing
    a new subclass. Pipeline code depends only on this interface.
    """

    @abstractmethod
    def list_namespaces(self) -> list[str]:
        """List all customer namespace directories."""
        ...

    @abstractmethod
    def list_date_partitions(self, namespace: str) -> list[str]:
        """List date partition directories (timestamp=YYYY-MM-DD) under a namespace."""
        ...

    @abstractmethod
    def list_files(self, namespace: str, date_partition: str) -> list[dict]:
        """List files in a partition. Returns dicts with: path, filename, size_bytes."""
        ...

    @abstractmethod
    def read_file(self, path: str) -> bytes:
        """Read raw bytes from a file path."""
        ...

    @abstractmethod
    def write_file(self, path: str, content: bytes) -> None:
        """Write bytes to a file path, creating parent dirs as needed."""
        ...

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists at the given path."""
        ...

    @abstractmethod
    def file_stat(self, path: str) -> dict:
        """Get file metadata. Returns dict with: size_bytes, modified_at."""
        ...
