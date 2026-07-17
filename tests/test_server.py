"""In-memory integration tests for the Toolset demo server."""

import pytest
from server.server import mcp

from mcp import Client
from mcp.client import advertise
from mcp.server.toolsets import EXTENSION_ID

pytestmark = pytest.mark.anyio


async def test_pagination_demo_traverses_pages_without_changing_core_ops() -> None:
    """Demo: the pagination family spans pages while core-ops remains one complete page."""
    async with Client(mcp, mode="auto", extensions=[advertise(EXTENSION_ID)]) as client:
        core = await client.list_toolsets(name="core-ops")
        assert [(toolset.name, toolset.version) for toolset in core.toolsets] == [
            ("core-ops", "1.0.0"),
            ("core-ops", "1.1.0"),
            ("core-ops", "2.0.0"),
        ]
        assert core.next_cursor is None

        first = await client.list_toolsets(name="pagination-demo")
        assert [(toolset.name, toolset.version) for toolset in first.toolsets] == [
            ("pagination-demo", "1.0.0"),
            ("pagination-demo", "1.1.0"),
            ("pagination-demo", "1.2.0"),
        ]
        assert first.next_cursor is not None

        second = await client.list_toolsets(cursor=first.next_cursor)
        assert [(toolset.name, toolset.version) for toolset in second.toolsets] == [("pagination-demo", "1.3.0")]
        assert second.next_cursor is None
