from __future__ import annotations


class DocIngestError(RuntimeError):
    """Base error for doc-ingest-mcp."""


class MissingDependencyError(DocIngestError):
    """Raised when an optional runtime dependency is unavailable."""

    def __init__(self, dependency: str, install_hint: str) -> None:
        super().__init__(f"{dependency} is not installed. {install_hint}")
        self.dependency = dependency
        self.install_hint = install_hint


class UnsupportedInputError(DocIngestError):
    """Raised when the user passes an unsupported source file."""


