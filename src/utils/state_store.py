from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from src.models import DiscoveredFile, PipelineRun, ProcessedEmail, SkippedFile


class StateStore:
    """SQLite-backed pipeline state. Survives crashes and restarts."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS processed_files (
                content_hash TEXT PRIMARY KEY,
                uid TEXT NOT NULL,
                source_path TEXT,
                namespace TEXT,
                date_partition TEXT,
                output_path TEXT,
                lineage_json TEXT,
                processed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS skipped_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT,
                reason TEXT,
                namespace TEXT,
                date_partition TEXT,
                discovered_at TEXT
            );

            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                mode TEXT,
                started_at TEXT,
                completed_at TEXT,
                status TEXT,
                files_discovered INTEGER DEFAULT 0,
                files_processed INTEGER DEFAULT 0,
                files_skipped INTEGER DEFAULT 0,
                files_deduplicated INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS discovered_files (
                content_hash TEXT,
                path TEXT,
                namespace TEXT,
                date_partition TEXT,
                discovered_at TEXT,
                PRIMARY KEY (content_hash, path)
            );
        """)

    def is_file_processed(self, content_hash: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM processed_files WHERE content_hash = ?", (content_hash,)
        ).fetchone()
        return row is not None

    def mark_file_processed(self, email: ProcessedEmail) -> None:
        lineage_json = email.source_lineage.model_dump_json()
        self._conn.execute(
            """INSERT OR IGNORE INTO processed_files
               (content_hash, uid, source_path, namespace,
                date_partition, output_path, lineage_json, processed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                email.content_hash,
                email.uid,
                email.source_lineage.source_file,
                email.source_lineage.namespace,
                email.source_lineage.date_partition,
                email.output_path,
                lineage_json,
                email.processed_at.isoformat(),
            ),
        )
        self._conn.commit()

    def record_skipped(self, skipped: SkippedFile) -> None:
        self._conn.execute(
            """INSERT INTO skipped_files (path, reason, namespace, date_partition, discovered_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                skipped.path,
                skipped.reason,
                skipped.namespace,
                skipped.date_partition,
                skipped.discovered_at.isoformat(),
            ),
        )
        self._conn.commit()

    def start_run(self, run_id: str, mode: str) -> None:
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            """INSERT INTO pipeline_runs (run_id, mode, started_at, status)
               VALUES (?, ?, ?, 'running')""",
            (run_id, mode, now),
        )
        self._conn.commit()

    def complete_run(self, run_id: str, stats: dict) -> None:
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            """UPDATE pipeline_runs
               SET completed_at = ?, status = 'completed',
                   files_discovered = ?, files_processed = ?,
                   files_skipped = ?, files_deduplicated = ?
               WHERE run_id = ?""",
            (
                now,
                stats.get("discovered", 0),
                stats.get("processed", 0),
                stats.get("skipped", 0),
                stats.get("deduplicated", 0),
                run_id,
            ),
        )
        self._conn.commit()

    def get_last_successful_run(self) -> PipelineRun | None:
        row = self._conn.execute(
            """SELECT * FROM pipeline_runs
               WHERE status = 'completed'
               ORDER BY completed_at DESC LIMIT 1"""
        ).fetchone()
        if not row:
            return None
        return PipelineRun(
            run_id=row["run_id"],
            mode=row["mode"],
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
            ),
            files_discovered=row["files_discovered"],
            files_processed=row["files_processed"],
            files_skipped=row["files_skipped"],
            files_deduplicated=row["files_deduplicated"],
        )

    def is_source_discovered(self, content_hash: str, path: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM discovered_files WHERE content_hash = ? AND path = ?",
            (content_hash, path),
        ).fetchone()
        return row is not None

    def mark_source_discovered(self, file: DiscoveredFile) -> None:
        self._conn.execute(
            """INSERT OR IGNORE INTO discovered_files
               (content_hash, path, namespace, date_partition, discovered_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                file.content_hash,
                file.path,
                file.namespace,
                file.date_partition,
                file.discovered_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_all_processed(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM processed_files").fetchall()
        results = []
        for row in rows:
            d = dict(row)
            if d.get("lineage_json"):
                d["lineage"] = json.loads(d["lineage_json"])
            results.append(d)
        return results

    def get_all_skipped(self) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM skipped_files").fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self._conn.close()
