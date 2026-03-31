from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from doc_ingest_mcp.cli import app


runner = CliRunner()


def test_ingest_cli_supports_fake_backend(tmp_path: Path, fixture_dir: Path) -> None:
    result = runner.invoke(
        app,
        [
            "ingest",
            str(fixture_dir / "scan.png"),
            "--out",
            str(tmp_path / "out"),
            "--backend",
            "fake",
        ],
    )
    assert result.exit_code == 0, result.output
    manifest = json.loads((tmp_path / "out" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "ok"


def test_export_cli_prints_markdown(tmp_path: Path, fixture_dir: Path) -> None:
    runner.invoke(
        app,
        [
            "ingest",
            str(fixture_dir / "contract.docx"),
            "--out",
            str(tmp_path / "sample"),
            "--backend",
            "fake",
        ],
    )
    result = runner.invoke(
        app,
        [
            "export",
            str(tmp_path / "sample"),
            "--format",
            "markdown",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Contract" in result.stdout or "contract" in result.stdout


def test_watch_cli_once_processes_existing_documents(tmp_path: Path, fixture_dir: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    for name in ["sample.pdf", "scan.png"]:
        (inbox / name).write_bytes((fixture_dir / name).read_bytes())

    result = runner.invoke(
        app,
        [
            "watch",
            str(inbox),
            "--out",
            str(tmp_path / "out"),
            "--backend",
            "fake",
            "--once",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "out" / "sample" / "manifest.json").exists()
    assert (tmp_path / "out" / "scan" / "manifest.json").exists()

