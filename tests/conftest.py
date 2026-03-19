from __future__ import annotations

from pathlib import Path

import pytest

from src.utils.file_provider import FileProvider
from src.utils.state_store import StateStore
from tests.fixtures.generate_fixtures import generate_all_fixtures


@pytest.fixture
def tmp_input_dir(tmp_path: Path) -> Path:
    """Create a temp directory populated with all test fixtures."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    generate_all_fixtures(input_dir)
    return input_dir


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def state_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_state.db"


@pytest.fixture
def storage(tmp_input_dir: Path) -> FileProvider:
    return FileProvider(tmp_input_dir)


@pytest.fixture
def state_store(state_db_path: Path) -> StateStore:
    store = StateStore(state_db_path)
    yield store
    store.close()


@pytest.fixture
def sample_eml_content() -> bytes:
    return (
        b"From: test@example.com\r\n"
        b"To: recipient@example.com\r\n"
        b"Subject: Sample\r\n"
        b"Date: Mon, 15 Jul 2024 10:00:00 +0000\r\n"
        b"Message-ID: <sample@example.com>\r\n"
        b"MIME-Version: 1.0\r\n"
        b'Content-Type: text/plain; charset="utf-8"\r\n'
        b"\r\n"
        b"Sample email body.\r\n"
    )


@pytest.fixture
def sample_html_content() -> bytes:
    return (
        b"<!DOCTYPE html>\n<html><body>"
        b"<p>From: test@example.com</p>"
        b"<p>Subject: HTML Sample</p>"
        b"</body></html>"
    )
