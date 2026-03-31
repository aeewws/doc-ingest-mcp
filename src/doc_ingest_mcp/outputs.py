from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from .types import BackendDocument, ChunkRecord, DocumentArtifact, IngestPaths, Manifest


def guess_mime_type(source: Path) -> str:
    mapping = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    return mapping.get(source.suffix.lower()) or mimetypes.guess_type(source.name)[0] or "application/octet-stream"


def estimate_tokens(text: str) -> int:
    words = [word for word in text.split() if word]
    return max(1, int(round(len(words) * 1.3))) if words else 1


def split_chunks(markdown: str) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    current_section = "body"
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        text = "\n".join(line.rstrip() for line in buffer).strip()
        if not text:
            buffer = []
            return
        chunks.append(
            ChunkRecord(
                id=f"chunk-{len(chunks) + 1:03d}",
                page=1,
                section=current_section,
                text=text,
                tokens_est=estimate_tokens(text),
            )
        )
        buffer = []

    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("#"):
            flush()
            current_section = stripped.lstrip("#").strip() or "body"
            continue
        buffer.append(stripped)
    flush()

    if not chunks and markdown.strip():
        chunks.append(
            ChunkRecord(
                id="chunk-001",
                page=1,
                section="body",
                text=markdown.strip(),
                tokens_est=estimate_tokens(markdown),
            )
        )
    return chunks


def build_artifact(source: Path, backend_doc: BackendDocument) -> DocumentArtifact:
    chunks = split_chunks(backend_doc.markdown)
    manifest = Manifest(
        source=str(source.resolve()),
        mime_type=guess_mime_type(source),
        page_count=max(1, backend_doc.page_count),
        ocr_used=backend_doc.ocr_used,
        chunk_count=len(chunks),
        table_count=len(backend_doc.table_markdowns),
        status="ok",
    )
    return DocumentArtifact(
        manifest=manifest,
        markdown=backend_doc.markdown,
        chunks=chunks,
        tables=backend_doc.table_markdowns,
        assets=[str(path) for path in backend_doc.asset_paths],
    )


def write_artifact(output_dir: Path, artifact: DocumentArtifact) -> IngestPaths:
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    tables_dir = output_dir / "tables"
    assets_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "manifest.json"
    markdown_path = output_dir / "document.md"
    chunks_path = output_dir / "chunks.jsonl"

    manifest_path.write_text(artifact.manifest.model_dump_json(indent=2), encoding="utf-8")
    markdown_path.write_text(artifact.markdown.rstrip() + "\n", encoding="utf-8")
    chunks_path.write_text(
        "\n".join(chunk.model_dump_json() for chunk in artifact.chunks) + ("\n" if artifact.chunks else ""),
        encoding="utf-8",
    )

    for index, table_markdown in enumerate(artifact.tables, start=1):
        (tables_dir / f"table-{index:03d}.md").write_text(table_markdown.rstrip() + "\n", encoding="utf-8")

    for asset in artifact.assets:
        asset_path = Path(asset)
        if asset_path.exists() and asset_path.is_file():
            target = assets_dir / asset_path.name
            if not target.exists():
                target.write_bytes(asset_path.read_bytes())

    return IngestPaths(
        output_dir=str(output_dir),
        manifest_path=str(manifest_path),
        markdown_path=str(markdown_path),
        chunks_path=str(chunks_path),
        assets_dir=str(assets_dir),
        tables_dir=str(tables_dir),
    )


def export_payload(output_dir: Path, format_name: str) -> str:
    format_name = format_name.lower()
    manifest_path = output_dir / "manifest.json"
    markdown_path = output_dir / "document.md"
    chunks_path = output_dir / "chunks.jsonl"

    if not manifest_path.exists() or not markdown_path.exists() or not chunks_path.exists():
        raise FileNotFoundError(f"{output_dir} does not look like a doc-ingest output directory.")

    if format_name == "markdown":
        return markdown_path.read_text(encoding="utf-8")
    if format_name == "chunks":
        return chunks_path.read_text(encoding="utf-8")
    if format_name == "json":
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        payload = {"manifest": manifest, "chunks": chunks}
        return json.dumps(payload, indent=2, ensure_ascii=False)
    raise ValueError("format must be markdown, chunks, or json")

