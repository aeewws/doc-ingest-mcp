from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Iterable

from .backend import extract_document
from .outputs import build_artifact, export_payload, write_artifact
from .types import IngestResult

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx"}
logger = logging.getLogger(__name__)


def _default_backend() -> str:
    return os.environ.get("DOC_INGEST_MCP_BACKEND", "auto")


def _target_dir_for_source(source: Path, output_root: Path | None) -> Path:
    if output_root is None:
        return source.parent / "out" / source.stem
    return output_root


def _iter_sources(root: Path, recursive: bool = True) -> Iterable[Path]:
    iterator = root.rglob("*") if recursive else root.iterdir()
    for path in iterator:
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def ingest_file(
    source: Path,
    output_dir: Path | None = None,
    backend: str | None = None,
) -> IngestResult:
    backend_name = backend or _default_backend()
    started = time.perf_counter()
    backend_doc = extract_document(source, backend=backend_name)
    artifact = build_artifact(source, backend_doc)
    artifact.manifest.duration_ms = max(1, int((time.perf_counter() - started) * 1000))
    target_dir = _target_dir_for_source(source, output_dir)
    paths = write_artifact(target_dir, artifact)
    return IngestResult(artifact=artifact, paths=paths)


def batch_ingest(
    source_dir: Path,
    output_root: Path | None = None,
    backend: str | None = None,
    recursive: bool = True,
) -> list[IngestResult]:
    results: list[IngestResult] = []
    for source in _iter_sources(source_dir, recursive=recursive):
        relative = source.relative_to(source_dir)
        target_dir = (output_root / relative).with_suffix("") if output_root is not None else None
        results.append(ingest_file(source, output_dir=target_dir, backend=backend))
    return results


def watch_inbox(
    source_dir: Path,
    output_root: Path | None = None,
    backend: str | None = None,
    poll_seconds: float = 2.0,
    once: bool = False,
) -> list[IngestResult]:
    processed: set[Path] = set()
    all_results: list[IngestResult] = []

    def scan() -> None:
        for source in _iter_sources(source_dir, recursive=True):
            if source in processed:
                continue
            relative = source.relative_to(source_dir)
            target_dir = (output_root / relative).with_suffix("") if output_root is not None else None
            try:
                all_results.append(ingest_file(source, output_dir=target_dir, backend=backend))
            except Exception:
                logger.exception("Failed to ingest %s while watching %s", source, source_dir)
                continue
            processed.add(source)

    scan()
    if once:
        return all_results

    while True:
        time.sleep(poll_seconds)
        scan()


def export_directory(source_dir: Path, format_name: str, output_file: Path | None = None) -> str:
    payload = export_payload(source_dir, format_name)
    if output_file is not None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(payload, encoding="utf-8")
    return payload

