from __future__ import annotations

import json
from pathlib import Path

from doc_ingest_mcp.mcp_server import build_tool_registry
from doc_ingest_mcp.pipeline import batch_ingest, export_directory, ingest_file


def test_ingest_writes_expected_contract(tmp_path: Path, fixture_dir: Path) -> None:
    source = fixture_dir / "sample.pdf"
    result = ingest_file(source, output_dir=tmp_path / "sample", backend="fake")

    manifest_path = Path(result.paths.manifest_path)
    markdown_path = Path(result.paths.markdown_path)
    chunks_path = Path(result.paths.chunks_path)
    tables_dir = Path(result.paths.tables_dir)

    assert manifest_path.exists()
    assert markdown_path.exists()
    assert chunks_path.exists()
    assert tables_dir.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["source"].endswith("sample.pdf")
    assert manifest["status"] == "ok"
    assert manifest["chunk_count"] >= 1
    assert manifest["table_count"] == 1
    assert "Alpha paragraph." in markdown_path.read_text(encoding="utf-8")
    assert "Beta paragraph." in (tables_dir / "table-001.md").read_text(encoding="utf-8")


def test_batch_ingest_processes_three_sample_documents(tmp_path: Path, fixture_dir: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    for name in ["sample.pdf", "scan.png", "contract.docx"]:
        (inbox / name).write_bytes((fixture_dir / name).read_bytes())

    results = batch_ingest(inbox, output_root=tmp_path / "out", backend="fake")
    assert len(results) == 3
    assert all(Path(result.paths.output_dir).exists() for result in results)


def test_export_reads_generated_output(tmp_path: Path, fixture_dir: Path) -> None:
    result = ingest_file(fixture_dir / "contract.docx", output_dir=tmp_path / "sample", backend="fake")
    payload = export_directory(Path(result.paths.output_dir), "json")
    data = json.loads(payload)
    assert data["manifest"]["status"] == "ok"
    assert data["chunks"]
    assert "Clause one." in Path(result.paths.markdown_path).read_text(encoding="utf-8")


def test_tool_registry_names_are_stable() -> None:
    registry = build_tool_registry()
    assert list(registry) == [
        "ingest_document",
        "batch_ingest",
        "get_manifest",
        "read_chunks",
        "export_markdown",
    ]
