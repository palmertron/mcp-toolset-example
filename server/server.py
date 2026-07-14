"""Streamable HTTP MCP server demonstrating Toolset Versioning pins.

Publishes three immutable `core-ops` Toolset versions over tools ToolA–ToolD.
Clients pin via `tools/list` / `tools/call` (`toolset: {name, version}`).
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from mcp.server.toolsets import Toolsets

toolsets = Toolsets()
mcp = MCPServer("toolset-demo", extensions=[toolsets])


@mcp.tool()
def ToolA() -> str:
    """Gets A content."""
    return "Tool A response"


@mcp.tool()
def ToolB() -> str:
    """Gets B content."""
    return "Tool B response"


@mcp.tool()
def ToolC() -> str:
    """Gets C content."""
    return "Tool C response"


@mcp.tool()
def ToolD() -> str:
    """Gets D content."""
    return "Tool D response"


toolsets.add_toolset(
    name="core-ops",
    version="1.0.0",
    status="stable",
    title="Core Ops",
    description="Baseline ops surface (A, B).",
    tools=["ToolA", "ToolB"],
)
toolsets.add_toolset(
    name="core-ops",
    version="1.1.0",
    status="stable",
    title="Core Ops",
    description="Minor additive release (A, B, C). Demo client pins here.",
    tools=["ToolA", "ToolB", "ToolC"],
)
toolsets.add_toolset(
    name="core-ops",
    version="2.0.0",
    status="stable",
    title="Core Ops",
    description="Major surface change (B, C, D; A removed).",
    tools=["ToolB", "ToolC", "ToolD"],
)


def main() -> None:
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
