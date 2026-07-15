"""No-LLM pin assertions against the running Toolset demo server.

Requires the Streamable HTTP server (``python -m server.server``).
Exit code 0 on success; prints failed assertion details and exits 1 on failure.
"""

from __future__ import annotations

import sys

import anyio
from mcp_types import TextContent, ToolsetRef

from mcp import Client, MCPError
from mcp.client import advertise
from mcp.server.toolsets import EXTENSION_ID, TOOLSET_ERROR

from client._config import mcp_url


def _names(tools: list) -> set[str]:
    return {t.name for t in tools}


async def _run() -> None:
    url = mcp_url()
    pin_100 = ToolsetRef(name="core-ops", version="1.0.0")
    pin_110 = ToolsetRef(name="core-ops", version="1.1.0")
    pin_200 = ToolsetRef(name="core-ops", version="2.0.0")

    async with Client(url, extensions=[advertise(EXTENSION_ID)]) as client:
        published = await client.list_toolsets(name="core-ops")
        assert {(t.name, t.version) for t in published.toolsets} == {
            ("core-ops", "1.0.0"),
            ("core-ops", "1.1.0"),
            ("core-ops", "2.0.0"),
        }, f"unexpected toolsets: {published.toolsets}"

        unpinned = await client.list_tools()
        assert _names(unpinned.tools) == {"ToolA", "ToolB", "ToolC", "ToolD"}, (
            f"unpinned catalog: {_names(unpinned.tools)}"
        )

        assert _names((await client.list_tools(toolset=pin_100)).tools) == {"ToolA", "ToolB"}
        assert _names((await client.list_tools(toolset=pin_110)).tools) == {"ToolA", "ToolB", "ToolC"}
        assert _names((await client.list_tools(toolset=pin_200)).tools) == {"ToolB", "ToolC", "ToolD"}

        try:
            await client.call_tool("ToolD", {}, toolset=pin_110)
            raise AssertionError("expected ToolD under 1.1.0 to raise MCPError")
        except MCPError as exc:
            assert exc.code == TOOLSET_ERROR
            assert exc.data["reason"] == "tool_not_in_toolset"

        unknown = ToolsetRef(name="core-ops", version="9.9.9")
        try:
            await client.call_tool("ToolA", {}, toolset=unknown)
            raise AssertionError("expected unknown pin on call to raise MCPError")
        except MCPError as exc:
            assert exc.code == TOOLSET_ERROR
            assert exc.data["reason"] == "unknown_toolset"

        ok = await client.call_tool("ToolA", {}, toolset=pin_110)
        assert ok.is_error is False
        assert isinstance(ok.content[0], TextContent)
        assert ok.content[0].text == "Tool A response"

    print("verify: all Toolset pin assertions passed")


def main() -> None:
    try:
        anyio.run(_run)
    except AssertionError as exc:
        print(f"verify FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except Exception as exc:
        print(f"verify ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
