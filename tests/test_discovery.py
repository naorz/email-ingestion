from __future__ import annotations

from src.discovery import detect_format, discover_files, scan_all
from src.models import FileFormat

NS = "test_namespace"
PART = "timestamp=2024-07-15"


class TestDetectFormat:
    def test_eml(self):
        assert detect_format("email.eml") == FileFormat.EML

    def test_html(self):
        assert detect_format("email.html") == FileFormat.HTML

    def test_htm(self):
        assert detect_format("email.htm") == FileFormat.HTML

    def test_msg(self):
        assert detect_format("email.msg") == FileFormat.MSG

    def test_mbox(self):
        assert detect_format("archive.mbox") == FileFormat.MBOX

    def test_pst(self):
        assert detect_format("archive.pst") == FileFormat.PST

    def test_zip(self):
        assert detect_format("archive.zip") == FileFormat.ZIP

    def test_unknown_extension(self):
        assert detect_format("photo.png") == FileFormat.UNKNOWN

    def test_case_insensitive(self):
        assert detect_format("EMAIL.EML") == FileFormat.EML
        assert detect_format("Archive.ZIP") == FileFormat.ZIP
        assert detect_format("Data.HTML") == FileFormat.HTML

    def test_no_extension(self):
        assert detect_format("noextension") == FileFormat.UNKNOWN


class TestDiscoverFiles:
    def test_discovers_all_files_in_partition(self, storage, state_store):
        files = discover_files(storage, state_store, NS, PART, "backfill")
        filenames = {f.filename for f in files}
        assert "email.eml" in filenames
        assert "mailbox_a.mbox" in filenames
        assert "photo.png" in filenames

    def test_incremental_skips_already_discovered(self, storage, state_store):
        first = discover_files(storage, state_store, NS, PART, "backfill")
        assert len(first) > 0
        second = discover_files(storage, state_store, NS, PART, "incremental")
        assert len(second) == 0

    def test_backfill_reprocesses_even_if_discovered(self, storage, state_store):
        first = discover_files(storage, state_store, NS, PART, "backfill")
        count1 = len(first)
        second = discover_files(storage, state_store, NS, PART, "backfill")
        assert len(second) == count1

    def test_unknown_format_detected(self, storage, state_store):
        files = discover_files(storage, state_store, NS, PART, "backfill")
        png_files = [f for f in files if f.filename == "photo.png"]
        assert len(png_files) == 1
        assert png_files[0].format == FileFormat.UNKNOWN


class TestScanAll:
    def test_scans_all_namespaces_and_partitions(self, storage, state_store):
        all_files = scan_all(storage, state_store, "backfill")
        namespaces = {f.namespace for f in all_files}
        assert "test_namespace" in namespaces
        partitions = {f.date_partition for f in all_files}
        assert "2024-07-15" in partitions
        assert "2024-07-16" in partitions
        assert "2024-07-17" in partitions
