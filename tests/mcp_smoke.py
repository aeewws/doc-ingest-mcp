from __future__ import annotations

import json
import tempfile
from pathlib import Path

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> None:
    source = Path("tests/fixtures/sample.pdf").resolve()
    output_dir = Path(tempfile.mkdtemp(prefix="doc-ingest-mcp-smoke-")) / "sample"

    server = StdioServerParameters(command="doc-ingest", args=["serve-mcp"])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            assert "ingest_document" in tool_names
            assert "export_markdown" in tool_names

            ingest_result = await session.call_tool(
                "ingest_document",
                {
                    "source": str(source),
                    "out": str(output_dir),
                    "backend": "fake",
                },
            )
            ingest_payload = next(item.text for item in ingest_result.content if item.type == "text")
            ingest_data = json.loads(ingest_payload)
            assert ingest_data["artifact"]["manifest"]["status"] == "ok"

            export_result = await session.call_tool(
                "export_markdown",
                {
                    "output_dir": str(output_dir),
                },
            )
            export_payload = next(item.text for item in export_result.content if item.type == "text")
            export_data = json.loads(export_payload)
            assert "Document title" in export_data["markdown"]


if __name__ == "__main__":
    anyio.run(main)
