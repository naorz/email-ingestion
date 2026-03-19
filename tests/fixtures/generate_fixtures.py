"""Programmatic generation of all test fixtures for edge-case testing."""

from __future__ import annotations

import io
import mailbox
import tempfile
import zipfile
from pathlib import Path


def _make_eml(
    from_addr: str = "test@example.com",
    to_addr: str = "recipient@example.com",
    subject: str = "Test Email",
    body: str = "This is a test email.",
    message_id: str | None = None,
) -> bytes:
    """Create a minimal valid EML file."""
    mid = message_id or f"<{subject.lower().replace(' ', '-')}@example.com>"
    return (
        f"From: {from_addr}\r\n"
        f"To: {to_addr}\r\n"
        f"Subject: {subject}\r\n"
        f"Date: Mon, 15 Jul 2024 10:00:00 +0000\r\n"
        f"Message-ID: {mid}\r\n"
        f"MIME-Version: 1.0\r\n"
        f'Content-Type: text/plain; charset="utf-8"\r\n'
        f"\r\n"
        f"{body}\r\n"
    ).encode()


def _make_eml_with_attachment(
    subject: str = "Email With Attachment",
    attachment_name: str = "document.txt",
    attachment_content: bytes = b"attachment content here",
) -> bytes:
    """Create an EML with a MIME attachment."""
    boundary = "----=_Part_12345"
    mid = f"<{subject.lower().replace(' ', '-')}@example.com>"
    return (
        f"From: sender@example.com\r\n"
        f"To: recipient@example.com\r\n"
        f"Subject: {subject}\r\n"
        f"Date: Mon, 15 Jul 2024 10:00:00 +0000\r\n"
        f"Message-ID: {mid}\r\n"
        f"MIME-Version: 1.0\r\n"
        f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n'
        f"\r\n"
        f"--{boundary}\r\n"
        f'Content-Type: text/plain; charset="utf-8"\r\n'
        f"\r\n"
        f"Email body text.\r\n"
        f"\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: application/octet-stream\r\n"
        f'Content-Disposition: attachment; filename="{attachment_name}"\r\n'
        f"Content-Transfer-Encoding: base64\r\n"
        f"\r\n"
        f"{__import__('base64').b64encode(attachment_content).decode()}\r\n"
        f"--{boundary}--\r\n"
    ).encode()


def _make_html_email() -> bytes:
    return (
        b"<!DOCTYPE html>\n<html>\n<head>\n"
        b'<meta charset="utf-8">\n'
        b"<title>Test HTML Email</title>\n"
        b"</head>\n<body>\n"
        b"<p><strong>From:</strong> test@example.com</p>\n"
        b"<p><strong>Subject:</strong> HTML Test</p>\n"
        b"<p>This is a test HTML email.</p>\n"
        b"</body>\n</html>\n"
    )


def _make_mbox(messages: list[tuple[str, str, str, str]]) -> bytes:
    """Create an MBOX file with the given messages.

    Each message is (from_addr, to_addr, subject, message_id).
    """
    with tempfile.NamedTemporaryFile(suffix=".mbox", delete=False) as tmp:
        tmp_path = tmp.name

    mbox = mailbox.mbox(tmp_path)
    for from_addr, to_addr, subject, msg_id in messages:
        eml_content = _make_eml(from_addr, to_addr, subject, f"Body of: {subject}", msg_id)
        msg = mailbox.mboxMessage(eml_content)
        mbox.add(msg)
    mbox.close()

    content = Path(tmp_path).read_bytes()
    Path(tmp_path).unlink()
    return content


def _make_zip(files: dict[str, bytes]) -> bytes:
    """Create a ZIP archive with the given filename→content pairs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _make_empty_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w"):
        pass
    return buf.getvalue()


def _make_password_protected_zip() -> bytes:
    """Create a password-protected ZIP using pyzipper (AES encryption)."""
    import pyzipper

    buf = io.BytesIO()
    with pyzipper.AESZipFile(
        buf, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES
    ) as zf:
        zf.setpassword(b"secret123")
        zf.writestr("secret_email.eml", _make_eml(subject="Secret Email"))
    return buf.getvalue()


def generate_all_fixtures(base_dir: Path) -> None:
    """Generate all test fixtures organized as namespace/timestamp=date/files."""

    ns = base_dir / "test_namespace"

    # --- Partition 1: timestamp=2024-07-15 ---
    p1 = ns / "timestamp=2024-07-15"
    p1.mkdir(parents=True, exist_ok=True)

    # Edge case 1: Same filename in different partitions (different content)
    (p1 / "email.eml").write_bytes(
        _make_eml(subject="Partition 1 Email", message_id="<p1-email@example.com>")
    )

    # Edge case 3: Two MBOXes with messages that could have same filenames
    (p1 / "mailbox_a.mbox").write_bytes(
        _make_mbox(
            [
                ("alice@ex.com", "bob@ex.com", "Thread A Msg 1", "<thread-a-1@ex.com>"),
                ("alice@ex.com", "bob@ex.com", "Thread A Msg 2", "<thread-a-2@ex.com>"),
            ]
        )
    )
    (p1 / "mailbox_b.mbox").write_bytes(
        _make_mbox(
            [
                ("carol@ex.com", "dave@ex.com", "Thread B Msg 1", "<thread-b-1@ex.com>"),
                ("carol@ex.com", "dave@ex.com", "Thread B Msg 2", "<thread-b-2@ex.com>"),
            ]
        )
    )

    # Edge case 4: Password-protected ZIP
    (p1 / "protected.zip").write_bytes(_make_password_protected_zip())

    # Edge case 5: Corrupted ZIP
    (p1 / "corrupted.zip").write_bytes(b"this is not a zip file at all, just random bytes!!")

    # Edge case 6: Non-email files mixed in
    (p1 / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
    (p1 / "data.xlsx").write_bytes(b"PK\x03\x04" + b"\x00" * 50)  # fake xlsx
    (p1 / "valid_alongside.eml").write_bytes(
        _make_eml(subject="Valid Email Among Junk", message_id="<valid-junk@example.com>")
    )

    # Edge case 7: Empty containers
    (p1 / "empty.zip").write_bytes(_make_empty_zip())
    (p1 / "empty.mbox").write_bytes(b"")

    # Edge case 8: EML with attachment
    (p1 / "with_attachment.eml").write_bytes(
        _make_eml_with_attachment(
            subject="Has Attachment",
            attachment_name="report.pdf",
            attachment_content=b"%PDF-1.4 fake pdf content",
        )
    )

    # --- Partition 2: timestamp=2024-07-16 ---
    p2 = ns / "timestamp=2024-07-16"
    p2.mkdir(parents=True, exist_ok=True)

    # Edge case 1: Same filename as partition 1 but different content
    (p2 / "email.eml").write_bytes(
        _make_eml(subject="Partition 2 Email", message_id="<p2-email@example.com>")
    )

    # Edge case 2: Nested ZIP (ZIP containing another ZIP containing emails)
    inner_zip = _make_zip(
        {
            "inner_email_1.eml": _make_eml(
                subject="Inner ZIP Email 1", message_id="<inner-1@ex.com>"
            ),
            "inner_email_2.eml": _make_eml(
                subject="Inner ZIP Email 2", message_id="<inner-2@ex.com>"
            ),
        }
    )
    outer_zip = _make_zip({"inner_archive.zip": inner_zip})
    (p2 / "nested.zip").write_bytes(outer_zip)

    # Edge case 10: Duplicate across partitions — same content as partition 1's email
    # This is a DIFFERENT file path but SAME content → tests global dedup
    (p2 / "duplicate_of_p1.eml").write_bytes(
        _make_eml(subject="Partition 1 Email", message_id="<p1-email@example.com>")
    )

    # --- Partition 3: timestamp=2024-07-17 ---
    p3 = ns / "timestamp=2024-07-17"
    p3.mkdir(parents=True, exist_ok=True)

    # Edge case 9: Deeply nested chain: ZIP → ZIP → MBOX → emails
    deep_mbox = _make_mbox(
        [
            ("deep@ex.com", "abyss@ex.com", "Deep Email 1", "<deep-1@ex.com>"),
            ("deep@ex.com", "abyss@ex.com", "Deep Email 2", "<deep-2@ex.com>"),
        ]
    )
    inner_zip_with_mbox = _make_zip({"deep.mbox": deep_mbox})
    outer_zip_deep = _make_zip({"level1.zip": inner_zip_with_mbox})
    (p3 / "deeply_nested.zip").write_bytes(outer_zip_deep)

    # An MSG file (deferred format — should be skipped)
    (p3 / "outlook_message.msg").write_bytes(b"\xd0\xcf\x11\xe0" + b"\x00" * 50)
