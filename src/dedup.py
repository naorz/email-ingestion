from __future__ import annotations

from src.utils.hashing import hash_content
from src.utils.state_store import StateStore


def generate_uid(content: bytes) -> str:
    """Generate a unique identifier for an email based on its content.

    Uses SHA-256 of the raw bytes. This means:
    - Same content → same UID (global dedup)
    - Different content with same filename → different UIDs
    - Same email delivered via different paths → deduplicated
    """
    return hash_content(content)


def is_duplicate(state: StateStore, content_hash: str) -> bool:
    """Check if an email with this content hash has already been processed."""
    return state.is_file_processed(content_hash)
