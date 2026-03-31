from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from .errors import DocIngestError
from .mcp_server import run_server
from .pipeline import batch_ingest, export_directory, ingest_file, watch_inbox

app = typer.Typer(add_completion=False, help="Ingest documents into a stable Markdown + manifest layout.")


def _print_exception(exc: Exception) -> None:
    typer.secho(str(exc), fg=typer.colors.RED, err=True)


def _result_summary(result) -> str:
    manifest = result.artifact.manifest
    return (
        f"{manifest.source}\n"
        f"output={result.paths.output_dir}\n"
        f"chunks={manifest.chunk_count} tables={manifest.table_count} "
        f"pages={manifest.page_count} status={manifest.status}"
    )


@app.command()
def ingest(
    source: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    out: Annotated[Path | None, typer.Option("--out", help="Output directory.")] = None,
    backend: Annotated[str, typer.Option("--backend", help="auto, fake, or docling.")] = "auto",
) -> None:
    try:
        result = ingest_file(source, output_dir=out, backend=backend)
    except DocIngestError as exc:
        _print_exception(exc)
        raise typer.Exit(code=1) from exc
    typer.echo(_result_summary(result))


@app.command()
def batch(
    source_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
    out: Annotated[Path | None, typer.Option("--out", help="Output root directory.")] = None,
    backend: Annotated[str, typer.Option("--backend", help="auto, fake, or docling.")] = "auto",
) -> None:
    failures = 0
    results = []
    for source in source_dir.rglob("*"):
        if not source.is_file():
            continue
        if source.suffix.lower() not in {".pdf", ".png", ".jpg", ".jpeg", ".docx"}:
            continue
        try:
            relative = source.relative_to(source_dir)
            target = (out / relative).with_suffix("") if out is not None else None
            result = ingest_file(source, output_dir=target, backend=backend)
            results.append(result)
            typer.echo(result.paths.output_dir)
        except Exception as exc:
            failures += 1
            typer.secho(f"{source}: {exc}", fg=typer.colors.RED, err=True)
    typer.echo(f"processed={len(results)} failures={failures}")
    if failures:
        raise typer.Exit(code=1)


@app.command()
def watch(
    source_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
    out: Annotated[Path | None, typer.Option("--out", help="Output root directory.")] = None,
    backend: Annotated[str, typer.Option("--backend", help="auto, fake, or docling.")] = "auto",
    poll_seconds: Annotated[float, typer.Option("--poll-seconds", min=0.1)] = 2.0,
    once: Annotated[bool, typer.Option("--once", help="Process current files and exit.")] = False,
) -> None:
    try:
        results = watch_inbox(source_dir, output_root=out, backend=backend, poll_seconds=poll_seconds, once=once)
    except DocIngestError as exc:
        _print_exception(exc)
        raise typer.Exit(code=1) from exc
    for result in results:
        typer.echo(result.paths.output_dir)


@app.command()
def export(
    source_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
    format: Annotated[str, typer.Option("--format", help="markdown, chunks, or json.")] = "markdown",
    out: Annotated[Path | None, typer.Option("--out", help="Optional output file.")] = None,
) -> None:
    try:
        payload = export_directory(source_dir, format, output_file=out)
    except Exception as exc:
        _print_exception(exc)
        raise typer.Exit(code=1) from exc
    if out is None:
        typer.echo(payload, nl=False)


@app.command("serve-mcp")
def serve_mcp() -> None:
    try:
        run_server()
    except DocIngestError as exc:
        _print_exception(exc)
        raise typer.Exit(code=1) from exc


def main() -> None:
    app()

