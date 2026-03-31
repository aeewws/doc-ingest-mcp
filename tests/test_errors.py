from __future__ import annotations

from pathlib import Path

import pytest

from doc_ingest_mcp.errors import MissingDependencyError, UnsupportedInputError
from doc_ingest_mcp.pipeline import ingest_file


def test_unsupported_input_is_clear(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("hello", encoding="utf-8")
    with pytest.raises(UnsupportedInputError):
        ingest_file(source, output_dir=tmp_path / "out", backend="fake")


def test_missing_docling_dependency_message_mentions_install_hint(fixture_dir: Path, tmp_path: Path) -> None:
    source = fixture_dir / "sample.pdf"
    with pytest.raises(MissingDependencyError) as excinfo:
        ingest_file(source, output_dir=tmp_path / "out", backend="docling")
    assert "pip install -e" in str(excinfo.value)


