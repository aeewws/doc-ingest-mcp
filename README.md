# doc-ingest-mcp

`doc-ingest-mcp` is a CLI and MCP server for turning documents into a stable
output bundle:

- `manifest.json`
- `document.md`
- `chunks.jsonl`
- `assets/`
- `tables/`

The default install stays light. Install the optional extras when you want the
full runtime:

```bash
pip install -e ".[dev]"
pip install -e ".[docling,mcp]"
```

## CLI

```bash
doc-ingest ingest ./sample.pdf --out ./out/sample --backend fake
doc-ingest batch ./incoming --out ./out --backend fake
doc-ingest watch ./incoming --out ./out --backend fake --once
doc-ingest export ./out/sample --format markdown
doc-ingest serve-mcp
```

`--backend fake` is the stable smoke-test mode used in this repository. It keeps
the tests deterministic even when Docling is not installed.

## Output Contract

Every successful ingest writes the same layout:

- `manifest.json`
- `document.md`
- `chunks.jsonl`
- `assets/`
- `tables/`

`manifest.json` includes:

- `source`
- `mime_type`
- `page_count`
- `ocr_used`
- `chunk_count`
- `table_count`
- `duration_ms`
- `status`
- `error`

`chunks.jsonl` stores one JSON object per chunk with:

- `id`
- `page`
- `section`
- `text`
- `tokens_est`

## Behavior

- `ingest` handles one file.
- `batch` processes supported files in a directory and keeps going if one file fails.
- `watch` polls an inbox and processes new files.
- `export` reads an output bundle and prints markdown, chunks, or JSON.
- `serve-mcp` exposes the same pipeline over MCP.

## Dependency Hints

- If Docling is missing, use `--backend fake` for smoke tests or install
  `pip install -e ".[docling]"`.
- If MCP support is missing, install `pip install -e ".[mcp]"`.

