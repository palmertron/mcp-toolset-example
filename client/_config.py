"""Shared env defaults for the demo client scripts."""

from __future__ import annotations

import os

from mcp_types import ToolsetRef

DEFAULT_MCP_URL = "http://127.0.0.1:8000/mcp"
DEFAULT_TOOLSET_NAME = "core-ops"
DEFAULT_TOOLSET_VERSION = "1.1.0"
DEFAULT_OPENAI_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_MODEL = "llama3.2"


def mcp_url() -> str:
    return os.environ.get("MCP_URL", DEFAULT_MCP_URL)


def toolset_pin() -> ToolsetRef:
    return ToolsetRef(
        name=os.environ.get("TOOLSET_NAME", DEFAULT_TOOLSET_NAME),
        version=os.environ.get("TOOLSET_VERSION", DEFAULT_TOOLSET_VERSION),
    )


def openai_base_url() -> str:
    return os.environ.get("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)


def openai_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "ollama")


def model_name() -> str:
    return os.environ.get("MODEL", DEFAULT_MODEL)
