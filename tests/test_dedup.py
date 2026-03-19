from __future__ import annotations

from datetime import UTC, datetime

from src.dedup import generate_uid, is_duplicate
from src.models import FileFormat, ProcessedEmail, SourceLineage
from src.utils.state_store import StateStore


class TestGenerateUid:
    def test_same_content_same_uid(self):
        content = b"identical email content"
        assert generate_uid(content) == generate_uid(content)

    def test_different_content_different_uid(self):
        uid1 = generate_uid(b"email content A")
        uid2 = generate_uid(b"email content B")
        assert uid1 != uid2

    def test_same_name_different_content_different_uid(self):
        # Simulates two PSTs both producing "001.eml" but with different content
        uid1 = generate_uid(b"From: alice@example.com\nSubject: Hello\n\nBody A")
        uid2 = generate_uid(b"From: bob@example.com\nSubject: World\n\nBody B")
        assert uid1 != uid2

    def test_uid_is_hex_string(self):
        uid = generate_uid(b"test content")
        assert len(uid) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in uid)


class TestIsDuplicate:
    def test_not_duplicate_initially(self, state_store: StateStore):
        assert not is_duplicate(state_store, "abc123hash")

    def test_duplicate_after_processing(self, state_store: StateStore):
        content_hash = generate_uid(b"some email content")

        # Mark as processed
        email = ProcessedEmail(
            uid=content_hash,
            source_lineage=SourceLineage(
                namespace="ns",
                date_partition="2024-07-15",
                source_file="test.eml",
                container_path=[],
                original_filename="test.eml",
            ),
            format=FileFormat.EML,
            content_hash=content_hash,
            output_path="ns/timestamp=2024-07-15/test.eml",
            has_attachments=False,
            processed_at=datetime.now(UTC),
        )
        state_store.mark_file_processed(email)

        assert is_duplicate(state_store, content_hash)

    def test_duplicate_across_runs(self, state_store: StateStore):
        """Same content processed in run 1 should be detected as duplicate in run 2."""
        content_hash = generate_uid(b"cross-run email")

        email = ProcessedEmail(
            uid=content_hash,
            source_lineage=SourceLineage(
                namespace="ns",
                date_partition="2024-07-15",
                source_file="email.eml",
                container_path=[],
                original_filename="email.eml",
            ),
            format=FileFormat.EML,
            content_hash=content_hash,
            output_path="ns/timestamp=2024-07-15/email.eml",
            has_attachments=False,
            processed_at=datetime.now(UTC),
        )
        state_store.mark_file_processed(email)

        # Simulates a new pipeline run checking the same content
        assert is_duplicate(state_store, content_hash)
