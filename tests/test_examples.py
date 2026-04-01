from __future__ import annotations

import json
from pathlib import Path


def test_checked_in_example_bundles_match_the_documented_contract() -> None:
    root = Path(__file__).resolve().parents[1] / "docs" / "examples"

    sample_pdf = root / "sample-pdf"
    contract_docx = root / "contract-docx"

    sample_manifest = json.loads((sample_pdf / "manifest.json").read_text(encoding="utf-8"))
    sample_markdown = (sample_pdf / "document.md").read_text(encoding="utf-8")
    sample_table = (sample_pdf / "tables" / "table-001.md").read_text(encoding="utf-8")

    contract_manifest = json.loads((contract_docx / "manifest.json").read_text(encoding="utf-8"))
    contract_markdown = (contract_docx / "document.md").read_text(encoding="utf-8")

    assert sample_manifest["status"] == "ok"
    assert sample_manifest["table_count"] == 1
    assert "Alpha paragraph." in sample_markdown
    assert "Beta paragraph." in sample_table

    assert contract_manifest["status"] == "ok"
    assert contract_manifest["table_count"] == 1
    assert "Clause one." in contract_markdown
