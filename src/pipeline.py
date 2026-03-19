from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from src.dedup import generate_uid, is_duplicate
from src.discovery import detect_format, scan_all
from src.models import (
    FileType,
    PipelineRun,
    ProcessedEmail,
    SkippedFile,
    SourceLineage,
)
from src.parsers import get_parser
from src.parsers.base import ParseResult
from src.utils.file_provider import FileProvider
from src.utils.state_store import StateStore


def run_pipeline(
    input_dir: str,
    output_dir: str,
    state_db: str,
    mode: str,
) -> PipelineRun:
    """Run the full ingestion pipeline.

    1. Discover files in input_dir
    2. Unpack containers recursively
    3. Deduplicate by content hash (global)
    4. Write individual emails to output_dir
    5. Write manifest.jsonl and skipped.jsonl
    """
    storage = FileProvider(input_dir)
    output = FileProvider(output_dir)
    state = StateStore(state_db)

    run_id = str(uuid.uuid4())
    state.start_run(run_id, mode)
    logger.info(f"Pipeline run {run_id} started (mode={mode})")

    # Phase 1: Discover
    discovered = scan_all(storage, state, mode)

    # Phase 2: Process each discovered file
    stats = {"discovered": len(discovered), "processed": 0, "skipped": 0, "deduplicated": 0}
    processed_emails: list[ProcessedEmail] = []
    skipped_files: list[SkippedFile] = []

    for file in discovered:
        content = storage.read_file(file.path)
        _process_file(
            content=content,
            filename=file.filename,
            namespace=file.namespace,
            date_partition=file.date_partition,
            source_file=file.filename,
            lineage=[],
            output=output,
            output_dir=output_dir,
            state=state,
            stats=stats,
            processed_emails=processed_emails,
            skipped_files=skipped_files,
        )

    # Phase 3: Write output manifests
    _write_manifest(output_dir, processed_emails)
    _write_skipped(output_dir, skipped_files)

    # Complete the run
    state.complete_run(run_id, stats)
    state.close()

    result = PipelineRun(
        run_id=run_id,
        mode=mode,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        files_discovered=stats["discovered"],
        files_processed=stats["processed"],
        files_skipped=stats["skipped"],
        files_deduplicated=stats["deduplicated"],
    )

    logger.info(
        f"Pipeline complete: {stats['processed']} processed, "
        f"{stats['skipped']} skipped, {stats['deduplicated']} deduplicated"
    )

    return result


def _process_file(
    content: bytes,
    filename: str,
    namespace: str,
    date_partition: str,
    source_file: str,
    lineage: list[str],
    output: FileProvider,
    output_dir: str,
    state: StateStore,
    stats: dict,
    processed_emails: list[ProcessedEmail],
    skipped_files: list[SkippedFile],
) -> None:
    """Process a single file — handles both single emails and containers recursively."""
    fmt = detect_format(filename)
    parser = get_parser(fmt)

    if parser is None:
        # Unsupported format
        if fmt.value in ("msg", "pst"):
            reason = f"{fmt.value}_not_supported"
        else:
            reason = "unsupported_format"
        skipped = SkippedFile(
            path=f"{namespace}/timestamp={date_partition}/{'/'.join([*lineage, filename])}",
            reason=reason,
            namespace=namespace,
            date_partition=date_partition,
            discovered_at=datetime.now(UTC),
        )
        state.record_skipped(skipped)
        skipped_files.append(skipped)
        stats["skipped"] += 1
        logger.debug(f"Skipped {filename}: {reason}")
        return

    # Parse the file
    result: ParseResult = parser.parse(content, filename, lineage)

    # Record any skipped items from parsing (e.g., password-protected entries)
    for skip_name, skip_reason in result.skipped:
        skipped = SkippedFile(
            path=f"{namespace}/timestamp={date_partition}/{skip_name}",
            reason=skip_reason,
            namespace=namespace,
            date_partition=date_partition,
            discovered_at=datetime.now(UTC),
        )
        state.record_skipped(skipped)
        skipped_files.append(skipped)
        stats["skipped"] += 1

    if parser.file_type == FileType.CONTAINER:
        # Container: each "email" in result might be another container or a leaf email
        for entry_filename, entry_content, entry_lineage in result.emails:
            _process_file(
                content=entry_content,
                filename=entry_filename,
                namespace=namespace,
                date_partition=date_partition,
                source_file=source_file,
                lineage=entry_lineage,
                output=output,
                output_dir=output_dir,
                state=state,
                stats=stats,
                processed_emails=processed_emails,
                skipped_files=skipped_files,
            )
    else:
        # Single email
        for email_filename, email_content, email_lineage in result.emails:
            uid = generate_uid(email_content)

            if is_duplicate(state, uid):
                stats["deduplicated"] += 1
                logger.debug(f"Duplicate skipped: {email_filename} (uid={uid[:12]}...)")
                continue

            # Determine output path
            ext = Path(email_filename).suffix or ".eml"
            rel_path = f"{namespace}/timestamp={date_partition}/{uid}{ext}"
            full_path = str(Path(output_dir) / rel_path)

            # Write the email
            output.write_file(full_path, email_content)

            # Write attachments if any
            attachment_dir = None
            if uid in result.attachments:
                att_dir = f"{namespace}/timestamp={date_partition}/{uid}_attachments"
                for att_name, att_content in result.attachments[uid]:
                    att_path = str(Path(output_dir) / att_dir / att_name)
                    output.write_file(att_path, att_content)
                attachment_dir = att_dir

            # Build lineage
            source_lineage = SourceLineage(
                namespace=namespace,
                date_partition=date_partition,
                source_file=source_file,
                container_path=email_lineage if email_lineage else [],
                original_filename=email_filename,
            )

            processed = ProcessedEmail(
                uid=uid,
                source_lineage=source_lineage,
                format=detect_format(email_filename),
                content_hash=uid,
                output_path=rel_path,
                has_attachments=attachment_dir is not None,
                attachment_dir=attachment_dir,
                processed_at=datetime.now(UTC),
            )

            state.mark_file_processed(processed)
            processed_emails.append(processed)
            stats["processed"] += 1
            logger.info(f"Processed: {email_filename} → {rel_path}")


def _write_manifest(output_dir: str, emails: list[ProcessedEmail]) -> None:
    """Write manifest.jsonl — one JSON object per processed email."""
    path = Path(output_dir) / "manifest.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for email in emails:
            f.write(email.model_dump_json() + "\n")
    logger.info(f"Wrote manifest: {path} ({len(emails)} entries)")


def _write_skipped(output_dir: str, skipped: list[SkippedFile]) -> None:
    """Write skipped.jsonl — one JSON object per skipped file."""
    path = Path(output_dir) / "skipped.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for s in skipped:
            f.write(s.model_dump_json() + "\n")
    logger.info(f"Wrote skipped: {path} ({len(skipped)} entries)")
