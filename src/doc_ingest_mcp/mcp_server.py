from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .errors import MissingDependencyError
from .pipeline import batch_ingest, export_directory, ingest_file


def build_tool_registry() -> dict[str, Callable[..., Any]]:
    return {
        "ingest_document": ingest_document,
        "batch_ingest": batch_ingest_documents,
        "get_manifest": get_manifest,
        "read_chunks": read_chunks,
        "export_markdown": export_markdown,
    }


def ingest_document(source: str, out: str | None = None, backend: str = "auto") -> dict:
    result = ingest_file(Path(source), Path(out) if out else None, backend=backend)
    return result.model_dump()


def batch_ingest_documents(source_dir: str, out: str | None = None, backend: str = "auto") -> dict:
    results = batch_ingest(Path(source_dir), Path(out) if out else None, backend=backend)
    return {"results": [result.model_dump() for result in results]}


def get_manifest(output_dir: str) -> dict:
    manifest_path = Path(output_dir) / "manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def read_chunks(output_dir: str) -> list[dict]:
    chunks_path = Path(output_dir) / "chunks.jsonl"
    return [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def export_markdown(output_dir: str) -> dict:
    payload = export_directory(Path(output_dir), "markdown")
    return {"markdown": payload}


def run_server() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - dependency path
        raise MissingDependencyError(
            "mcp",
            "Install the MCP extra with `pip install -e \".[mcp]\"` before using `serve-mcp`.",
        ) from exc

    server = FastMCP("doc-ingest-mcp")
    ingest_document_impl = globals()["ingest_document"]
    batch_ingest_documents_impl = globals()["batch_ingest_documents"]
    get_manifest_impl = globals()["get_manifest"]
    read_chunks_impl = globals()["read_chunks"]
    export_markdown_impl = globals()["export_markdown"]

    @server.tool()
    def ingest_document(source: str, out: str | None = None, backend: str = "auto") -> dict:
        return ingest_document_impl(source, out=out, backend=backend)

    @server.tool()
    def batch_ingest(source_dir: str, out: str | None = None, backend: str = "auto") -> dict:
        return batch_ingest_documents_impl(source_dir, out=out, backend=backend)

    @server.tool()
    def get_manifest(output_dir: str) -> dict:
        return get_manifest_impl(output_dir)

    @server.tool()
    def read_chunks(output_dir: str) -> list[dict]:
        return read_chunks_impl(output_dir)

    @server.tool()
    def export_markdown(output_dir: str) -> dict:
        return export_markdown_impl(output_dir)

    try:
        server.run(transport="stdio")
    except TypeError:
        server.run()

