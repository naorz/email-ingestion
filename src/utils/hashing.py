import hashlib


def hash_content(content: bytes) -> str:
    """SHA-256 hash of file content. Used for dedup and unique IDs."""
    return hashlib.sha256(content).hexdigest()
