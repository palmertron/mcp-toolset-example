# MCP Toolset Versioning — e2e demo

Companion demo for the [Toolset Versioning SEP draft](https://github.com/palmertron/modelcontextprotocol/blob/sep/toolset-versioning/seps/0000-toolset-versioning.md) and the Python SDK **draft reference** on branch [`feature/toolset-versioning`](https://github.com/palmertron/python-sdk/tree/feature/toolset-versioning).

A Streamable HTTP MCP server publishes three immutable `core-ops` Toolset versions. The demo targets MCP protocol revision `2026-07-28`: clients discover server support through `server/discover`, advertise `io.modelcontextprotocol/toolsets` in per-request capabilities, and pass an exact `toolset` pin on `tools/list` / `tools/call`. A CLI agent pins `core-ops@1.1.0` and drives tools through a local OpenAI-compatible LLM (Ollama by default).

## Layout

```
server/server.py   # MCPServer + Toolsets over Streamable HTTP
client/verify.py   # No-LLM pin assertions
client/agent.py    # CLI agent (Ollama / OpenAI-compatible)
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Sibling checkout of the SDK at `../python-sdk` on branch `feature/toolset-versioning`
- For the agent: [Ollama](https://ollama.com/) with a tools-capable model, e.g. `ollama pull llama3.2`

## Install

From this repo root:

```bash
uv sync
```

`pyproject.toml` depends on `mcp` via an editable path to `../python-sdk`.

## Run

**Terminal 1 — server**

```bash
uv run python -m server.server
```

Listens at `http://127.0.0.1:8000/mcp`.

**Terminal 2 — verify (no LLM)**

```bash
uv run python -m client.verify
```

Asserts unpinned vs pinned membership, that `ToolD` under `1.1.0` returns `tool_not_in_toolset`, and that an unknown pin returns `unknown_toolset` on `tools/call`.

**Terminal 2 — agent**

```bash
uv run python -m client.agent
```

Then try: `get me a content list`. The agent should call `ToolA`, `ToolB`, and `ToolC` only (never `ToolD` under the pin).

## Toolsets

| Version | Tools |
|---|---|
| `core-ops@1.0.0` | ToolA, ToolB |
| `core-ops@1.1.0` (agent pin) | ToolA, ToolB, ToolC |
| `core-ops@2.0.0` | ToolB, ToolC, ToolD |

Unpinned `tools/list` still returns ToolA–ToolD.

## Environment

| Variable | Default |
|---|---|
| `MCP_URL` | `http://127.0.0.1:8000/mcp` |
| `TOOLSET_NAME` | `core-ops` |
| `TOOLSET_VERSION` | `1.1.0` |
| `OPENAI_BASE_URL` | `http://127.0.0.1:11434/v1` |
| `OPENAI_API_KEY` | `ollama` |
| `MODEL` | `llama3.2` |

Point `OPENAI_BASE_URL` / `MODEL` at any OpenAI-compatible chat+tools endpoint.

## SEP framing

This demo shows the extension wire behavior that SEP reviewers may be interested in:

1. Discover server support through `server/discover` and advertise the extension in each extension-dependent request
2. `toolsets/list` discovery
3. Exact pin on `tools/list` / `tools/call`
4. Protocol errors for non-members (`tool_not_in_toolset`) and unknown pins (`unknown_toolset`)
5. Concurrent immutable versions (`1.0.0` / `1.1.0` / `2.0.0`) on one server
