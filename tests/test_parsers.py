from __future__ import annotations

import io
import zipfile

from src.models import FileFormat, FileType
from src.parsers import get_parser, is_supported
from src.parsers.eml_parser import EmlParser
from src.parsers.html_parser import HtmlParser
from src.parsers.mbox_parser import MboxParser
from src.parsers.zip_parser import ZipParser
from tests.fixtures.generate_fixtures import (
    _make_eml,
    _make_eml_with_attachment,
    _make_empty_zip,
    _make_html_email,
    _make_mbox,
    _make_password_protected_zip,
    _make_zip,
)


class TestParserRegistry:
    def test_get_parser_eml(self):
        parser = get_parser(FileFormat.EML)
        assert parser is not None
        assert isinstance(parser, EmlParser)

    def test_get_parser_html(self):
        assert isinstance(get_parser(FileFormat.HTML), HtmlParser)

    def test_get_parser_zip(self):
        assert isinstance(get_parser(FileFormat.ZIP), ZipParser)

    def test_get_parser_mbox(self):
        assert isinstance(get_parser(FileFormat.MBOX), MboxParser)

    def test_get_parser_msg_unsupported(self):
        assert get_parser(FileFormat.MSG) is None

    def test_get_parser_pst_unsupported(self):
        assert get_parser(FileFormat.PST) is None

    def test_is_supported(self):
        assert is_supported(FileFormat.EML)
        assert is_supported(FileFormat.ZIP)
        assert not is_supported(FileFormat.MSG)
        assert not is_supported(FileFormat.PST)
        assert not is_supported(FileFormat.UNKNOWN)


class TestEmlParser:
    def test_parse_returns_single_email(self):
        parser = EmlParser()
        content = _make_eml(subject="Test")
        result = parser.parse(content, "test.eml", [])
        assert len(result.emails) == 1
        filename, data, lineage = result.emails[0]
        assert filename == "test.eml"
        assert data == content
        assert lineage == []

    def test_parse_preserves_lineage(self):
        parser = EmlParser()
        content = _make_eml(subject="Nested")
        result = parser.parse(content, "nested.eml", ["archive.zip"])
        _, _, lineage = result.emails[0]
        assert lineage == ["archive.zip"]

    def test_extracts_attachments(self):
        parser = EmlParser()
        content = _make_eml_with_attachment(
            subject="With Attachment",
            attachment_name="report.pdf",
            attachment_content=b"pdf content",
        )
        result = parser.parse(content, "att.eml", [])
        assert len(result.emails) == 1
        assert len(result.attachments) == 1
        att_list = list(result.attachments.values())[0]
        assert att_list[0][0] == "report.pdf"

    def test_file_type(self):
        assert EmlParser().file_type == FileType.SINGLE_EMAIL

    def test_can_parse(self):
        parser = EmlParser()
        assert parser.can_parse("test.eml")
        assert parser.can_parse("TEST.EML")
        assert not parser.can_parse("test.html")


class TestHtmlParser:
    def test_parse_returns_single_email(self):
        parser = HtmlParser()
        content = _make_html_email()
        result = parser.parse(content, "test.html", [])
        assert len(result.emails) == 1
        assert result.emails[0][0] == "test.html"

    def test_can_parse_htm(self):
        parser = HtmlParser()
        assert parser.can_parse("test.htm")
        assert parser.can_parse("test.html")
        assert not parser.can_parse("test.eml")

    def test_file_type(self):
        assert HtmlParser().file_type == FileType.SINGLE_EMAIL


class TestZipParser:
    def test_unpack_simple_zip(self):
        parser = ZipParser()
        zip_content = _make_zip(
            {
                "email1.eml": _make_eml(subject="Zip Email 1"),
                "email2.eml": _make_eml(subject="Zip Email 2"),
            }
        )
        result = parser.parse(zip_content, "test.zip", [])
        assert len(result.emails) == 2
        filenames = {e[0] for e in result.emails}
        assert "email1.eml" in filenames
        assert "email2.eml" in filenames

    def test_builds_lineage(self):
        parser = ZipParser()
        zip_content = _make_zip({"inner.eml": _make_eml(subject="Inner")})
        result = parser.parse(zip_content, "outer.zip", ["parent.zip"])
        _, _, lineage = result.emails[0]
        assert lineage == ["parent.zip", "inner.eml"]

    def test_nested_zip(self):
        parser = ZipParser()
        inner_zip = _make_zip({"deep.eml": _make_eml(subject="Deep")})
        outer_zip = _make_zip({"inner.zip": inner_zip})
        result = parser.parse(outer_zip, "outer.zip", [])
        # ZIP parser extracts entries but doesn't recursively unpack — pipeline does that
        assert len(result.emails) == 1
        assert result.emails[0][0] == "inner.zip"

    def test_password_protected_zip(self):
        parser = ZipParser()
        content = _make_password_protected_zip()
        result = parser.parse(content, "protected.zip", [])
        assert len(result.skipped) > 0
        reasons = [reason for _, reason in result.skipped]
        assert any("password" in r for r in reasons)

    def test_corrupted_zip(self):
        parser = ZipParser()
        result = parser.parse(b"not a zip file!!", "bad.zip", [])
        assert len(result.skipped) == 1
        assert result.skipped[0][1] == "corrupted"

    def test_empty_zip(self):
        parser = ZipParser()
        result = parser.parse(_make_empty_zip(), "empty.zip", [])
        assert len(result.emails) == 0
        assert len(result.skipped) == 0

    def test_file_type(self):
        assert ZipParser().file_type == FileType.CONTAINER

    def test_skips_directories(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.mkdir("subdir")
            zf.writestr("subdir/email.eml", _make_eml(subject="In Dir"))
        parser = ZipParser()
        result = parser.parse(buf.getvalue(), "with_dir.zip", [])
        assert len(result.emails) == 1
        assert result.emails[0][0] == "subdir/email.eml"


class TestMboxParser:
    def test_extracts_multiple_messages(self):
        parser = MboxParser()
        content = _make_mbox(
            [
                ("a@ex.com", "b@ex.com", "Msg 1", "<msg-1@ex.com>"),
                ("a@ex.com", "b@ex.com", "Msg 2", "<msg-2@ex.com>"),
                ("a@ex.com", "b@ex.com", "Msg 3", "<msg-3@ex.com>"),
            ]
        )
        result = parser.parse(content, "test.mbox", [])
        assert len(result.emails) == 3

    def test_generates_filenames_from_message_id(self):
        parser = MboxParser()
        content = _make_mbox(
            [
                ("a@ex.com", "b@ex.com", "Test", "<unique-id-123@ex.com>"),
            ]
        )
        result = parser.parse(content, "test.mbox", [])
        filename = result.emails[0][0]
        assert "unique-id-123@ex.com" in filename
        assert filename.endswith(".eml")

    def test_fallback_filename_without_message_id(self):
        # Create an MBOX with a message that has no Message-ID
        raw = (
            b"From test@example.com Mon Jul 15 10:00:00 2024\n"
            b"From: test@example.com\n"
            b"To: recipient@example.com\n"
            b"Subject: No ID\n"
            b"\n"
            b"Body text.\n"
            b"\n"
        )
        parser = MboxParser()
        result = parser.parse(raw, "noid.mbox", [])
        assert len(result.emails) == 1
        assert result.emails[0][0].startswith("msg_")

    def test_empty_mbox(self):
        parser = MboxParser()
        result = parser.parse(b"", "empty.mbox", [])
        assert len(result.emails) == 0

    def test_builds_lineage(self):
        parser = MboxParser()
        content = _make_mbox([("a@ex.com", "b@ex.com", "Test", "<t@ex.com>")])
        result = parser.parse(content, "archive.mbox", ["batch.zip"])
        _, _, lineage = result.emails[0]
        assert "batch.zip" in lineage

    def test_file_type(self):
        assert MboxParser().file_type == FileType.CONTAINER
