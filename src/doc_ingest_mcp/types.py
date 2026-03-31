from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChunkRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    page: int = 1
    section: str = "body"
    text: str
    tokens_est: int = 0


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    mime_type: str
    page_count: int = 1
    ocr_used: bool = False
    chunk_count: int = 0
    table_count: int = 0
    duration_ms: int = 0
    status: Literal["ok", "error"] = "ok"
    error: str | None = None


class DocumentArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: Manifest
    markdown: str
    chunks: list[ChunkRecord] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)


class IngestPaths(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_dir: str
    manifest_path: str
    markdown_path: str
    chunks_path: str
    assets_dir: str
    tables_dir: str


class IngestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact: DocumentArtifact
    paths: IngestPaths


@dataclass(slots=True)
class BackendDocument:
    source: Path
    markdown: str
    page_count: int = 1
    ocr_used: bool = False
    table_markdowns: list[str] = field(default_factory=list)
    asset_paths: list[Path] = field(default_factory=list)

