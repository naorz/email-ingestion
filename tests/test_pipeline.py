from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.pipeline import run_pipeline


class TestPipelineIntegration:
    """Integration tests using the generated fixtures."""

    def test_full_backfill_run(self, tmp_input_dir, tmp_output_dir, state_db_path):
        result = run_pipeline(
            str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill"
        )
        assert result.files_discovered > 0
        assert result.files_processed > 0
        assert result.mode == "backfill"

    def test_manifest_created(self, tmp_input_dir, tmp_output_dir, state_db_path):
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        manifest = tmp_output_dir / "manifest.jsonl"
        assert manifest.exists()
        lines = manifest.read_text().strip().split("\n")
        assert len(lines) > 0
        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert "uid" in data
            assert "source_lineage" in data
            assert "output_path" in data

    def test_skipped_file_created(self, tmp_input_dir, tmp_output_dir, state_db_path):
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        skipped = tmp_output_dir / "skipped.jsonl"
        assert skipped.exists()

    def test_non_email_files_skipped(self, tmp_input_dir, tmp_output_dir, state_db_path):
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        skipped = tmp_output_dir / "skipped.jsonl"
        lines = skipped.read_text().strip().split("\n")
        skipped_data = [json.loads(line) for line in lines if line.strip()]

        # photo.png and data.xlsx should be skipped
        skipped_paths = [s["path"] for s in skipped_data]
        reasons = [s["reason"] for s in skipped_data]
        assert any("photo.png" in p for p in skipped_paths)
        assert "unsupported_format" in reasons

    def test_corrupted_zip_skipped(self, tmp_input_dir, tmp_output_dir, state_db_path):
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        skipped = tmp_output_dir / "skipped.jsonl"
        lines = skipped.read_text().strip().split("\n")
        skipped_data = [json.loads(line) for line in lines if line.strip()]
        reasons = [s["reason"] for s in skipped_data]
        assert "corrupted" in reasons

    def test_password_protected_zip_skipped(self, tmp_input_dir, tmp_output_dir, state_db_path):
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        skipped = tmp_output_dir / "skipped.jsonl"
        lines = skipped.read_text().strip().split("\n")
        skipped_data = [json.loads(line) for line in lines if line.strip()]
        reasons = [s["reason"] for s in skipped_data]
        assert any("password" in r for r in reasons)

    def test_msg_format_skipped(self, tmp_input_dir, tmp_output_dir, state_db_path):
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        skipped = tmp_output_dir / "skipped.jsonl"
        lines = skipped.read_text().strip().split("\n")
        skipped_data = [json.loads(line) for line in lines if line.strip()]
        reasons = [s["reason"] for s in skipped_data]
        assert "msg_not_supported" in reasons

    def test_same_filename_different_partitions_both_processed(
        self, tmp_input_dir, tmp_output_dir, state_db_path
    ):
        """Edge case 1: email.eml in both partitions both processed."""
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        manifest = tmp_output_dir / "manifest.jsonl"
        lines = manifest.read_text().strip().split("\n")
        entries = [json.loads(line) for line in lines]

        # Find entries that came from "email.eml"
        email_entries = [
            e for e in entries if e["source_lineage"]["original_filename"] == "email.eml"
        ]
        # Should have 2 entries (different content → different UIDs)
        # But with global dedup, the duplicate in p2 will be deduplicated
        # Actually: p1 email.eml and p2 email.eml have DIFFERENT subjects, so different UIDs
        assert len(email_entries) == 2

    def test_global_dedup_across_partitions(self, tmp_input_dir, tmp_output_dir, state_db_path):
        """Edge case 10: duplicate_of_p1.eml has same content as p1's email.eml → deduplicated."""
        result = run_pipeline(
            str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill"
        )
        assert result.files_deduplicated >= 1

    def test_nested_zip_unpacked(self, tmp_input_dir, tmp_output_dir, state_db_path):
        """Edge case 2: nested.zip → inner_archive.zip → 2 emails."""
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        manifest = tmp_output_dir / "manifest.jsonl"
        lines = manifest.read_text().strip().split("\n")
        entries = [json.loads(line) for line in lines]

        # Find entries from nested zip — they go through nested.zip → inner_archive.zip → emails
        nested_entries = [e for e in entries if e["source_lineage"]["source_file"] == "nested.zip"]
        assert len(nested_entries) == 2

    def test_deeply_nested_chain(self, tmp_input_dir, tmp_output_dir, state_db_path):
        """Edge case 9: ZIP → ZIP → MBOX → 2 emails."""
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        manifest = tmp_output_dir / "manifest.jsonl"
        lines = manifest.read_text().strip().split("\n")
        entries = [json.loads(line) for line in lines]

        # Find entries from deeply nested chain (ZIP → ZIP → MBOX → emails)
        deep_entries = [
            e for e in entries if e["source_lineage"]["source_file"] == "deeply_nested.zip"
        ]
        assert len(deep_entries) == 2
        # Lineage should trace back through ZIP → ZIP → MBOX → email
        for entry in deep_entries:
            lineage = entry["source_lineage"]["container_path"]
            assert len(lineage) >= 3

    def test_incremental_after_backfill_processes_zero(
        self, tmp_input_dir, tmp_output_dir, state_db_path
    ):
        """Running incremental after backfill should find 0 new files."""
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        result2 = run_pipeline(
            str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "incremental"
        )
        assert result2.files_discovered == 0
        assert result2.files_processed == 0

    def test_crash_recovery(self, tmp_input_dir, tmp_output_dir, state_db_path):
        """Edge case 8: Pipeline state persists — re-running skips already-processed emails."""
        result1 = run_pipeline(
            str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill"
        )
        processed_first = result1.files_processed

        # Simulate crash by running backfill again (state persists)
        result2 = run_pipeline(
            str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill"
        )
        # Backfill re-discovers but dedup prevents reprocessing any emails
        assert result2.files_deduplicated >= processed_first
        assert result2.files_processed == 0

    def test_two_mboxes_same_filenames_different_content(
        self, tmp_input_dir, tmp_output_dir, state_db_path
    ):
        """Edge case 3: mailbox_a and mailbox_b have different messages → different UIDs."""
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        manifest = tmp_output_dir / "manifest.jsonl"
        lines = manifest.read_text().strip().split("\n")
        entries = [json.loads(line) for line in lines]

        # Find entries from both mboxes (source_file tracks the original file)
        mbox_a = [e for e in entries if e["source_lineage"]["source_file"] == "mailbox_a.mbox"]
        mbox_b = [e for e in entries if e["source_lineage"]["source_file"] == "mailbox_b.mbox"]
        assert len(mbox_a) == 2
        assert len(mbox_b) == 2
        # All 4 should have different UIDs
        all_uids = {e["uid"] for e in mbox_a + mbox_b}
        assert len(all_uids) == 4

    def test_attachment_extraction(self, tmp_input_dir, tmp_output_dir, state_db_path):
        """Emails with attachments should have attachment_dir set."""
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        manifest = tmp_output_dir / "manifest.jsonl"
        lines = manifest.read_text().strip().split("\n")
        entries = [json.loads(line) for line in lines]

        with_att = [e for e in entries if e["has_attachments"]]
        assert len(with_att) >= 1
        for entry in with_att:
            assert entry["attachment_dir"] is not None
            att_dir = tmp_output_dir / entry["attachment_dir"]
            assert att_dir.exists()

    def test_output_directory_structure(self, tmp_input_dir, tmp_output_dir, state_db_path):
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        # Should have namespace/partition subdirs
        ns_dir = tmp_output_dir / "test_namespace"
        assert ns_dir.exists()
        partitions = [d.name for d in ns_dir.iterdir() if d.is_dir()]
        assert "timestamp=2024-07-15" in partitions

    def test_empty_containers_handled(self, tmp_input_dir, tmp_output_dir, state_db_path):
        """Edge case 7: empty.zip and empty.mbox should not produce any emails."""
        run_pipeline(str(tmp_input_dir), str(tmp_output_dir), str(state_db_path), "backfill")
        manifest = tmp_output_dir / "manifest.jsonl"
        lines = manifest.read_text().strip().split("\n")
        entries = [json.loads(line) for line in lines]

        # No entries should come from empty containers
        empty_entries = [e for e in entries if "empty" in e["source_lineage"]["source_file"]]
        assert len(empty_entries) == 0


class TestPipelineWithProvidedTestData:
    """Tests using the original test_data from the assignment."""

    @pytest.fixture
    def assignment_test_data(self) -> Path:
        path = Path(__file__).parent.parent / "_assignment" / "test_data"
        if not path.exists():
            pytest.skip("Assignment test_data not found")
        return path

    def test_processes_all_provided_fixtures(
        self, assignment_test_data, tmp_output_dir, state_db_path
    ):
        result = run_pipeline(
            str(assignment_test_data), str(tmp_output_dir), str(state_db_path), "backfill"
        )
        # 5 source files → 8 individual emails:
        # simple_email(1) + another_email.html(1) + batch.zip(2)
        # + conversations.mbox(3) + new_email.eml(1)
        assert result.files_discovered == 5
        assert result.files_processed == 8

    def test_manifest_has_correct_lineage(
        self, assignment_test_data, tmp_output_dir, state_db_path
    ):
        run_pipeline(str(assignment_test_data), str(tmp_output_dir), str(state_db_path), "backfill")
        manifest = tmp_output_dir / "manifest.jsonl"
        lines = manifest.read_text().strip().split("\n")
        entries = [json.loads(line) for line in lines]

        # Emails from batch.zip should have container_path mentioning zip entries
        zip_entries = [e for e in entries if e["source_lineage"]["source_file"] == "batch.zip"]
        assert len(zip_entries) == 2
        for entry in zip_entries:
            assert len(entry["source_lineage"]["container_path"]) > 0
