"""CLI agent that pins core-ops@1.1.0 and drives tools via a local OpenAI-compatible LLM.

Default model endpoint is Ollama (``http://127.0.0.1:11434/v1``). Override with
``OPENAI_BASE_URL``, ``OPENAI_API_KEY``, ``MODEL``, ``MCP_URL``, ``TOOLSET_*``.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import anyio
from mcp_types import TextContent, Tool, ToolsetRef
from openai import AsyncOpenAI

from mcp import Client
from mcp.client import advertise
from mcp.server.toolsets import EXTENSION_ID

from client._config import (
    mcp_url,
    model_name,
    openai_api_key,
    openai_base_url,
    toolset_pin,
)

SYSTEM_PROMPT = """\
You demonstrate MCP Toolset pinning. You may ONLY use the tools provided via the API.

If the user asks for content / a content list / all content / available content:
1. Call EVERY tool in your tool list exactly once. Do not invent tools. Do not skip any.
2. After tool results arrive, reply with ONLY this format (no intro, no apology, no "empty"):

Here is all the content I have access to:
- <tool name>: <exact tool result text>
- <tool name>: <exact tool result text>

Copy each tool result character-for-character from the tool message. Never say a result was empty if text was returned. Never invent sample JSON or HTML.

For any other user request: reply only that you demonstrate Toolset pins and ask them to request all content. Do not call tools for off-topic questions.
"""


def _tool_to_openai(tool: Tool) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema or {"type": "object", "properties": {}},
        },
    }


def _text_from_result(result: Any) -> str:
    parts: list[str] = []
    for block in result.content:
        if isinstance(block, TextContent):
            parts.append(block.text)
        else:
            parts.append(str(block))
    return "\n".join(parts) if parts else "(empty)"


async def _run() -> None:
    url = mcp_url()
    pin = toolset_pin()
    model = model_name()
    llm = AsyncOpenAI(base_url=openai_base_url(), api_key=openai_api_key())

    async with Client(url, extensions=[advertise(EXTENSION_ID)]) as client:
        listed = await client.list_tools(toolset=pin)
        openai_tools = [_tool_to_openai(t) for t in listed.tools]
        names = [t.name for t in listed.tools]

        print(f"MCP:      {url}")
        print(f"Pin:      {pin.name}@{pin.version}")
        print(f"Tools:    {', '.join(names)}")
        print(f"Model:    {model} @ {openai_base_url()}")
        print("Type a prompt (or 'quit'). Try: get me a content list\n")

        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        while True:
            try:
                user = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user:
                continue
            if user.lower() in {"quit", "exit", "q"}:
                break

            messages.append({"role": "user", "content": user})
            await _agent_turn(llm, client, model, openai_tools, pin, messages)


async def _agent_turn(
    llm: AsyncOpenAI,
    client: Client,
    model: str,
    openai_tools: list[dict[str, Any]],
    pin: ToolsetRef,
    messages: list[dict[str, Any]],
) -> None:
    for _ in range(8):
        response = await llm.chat.completions.create(
            model=model,
            messages=messages,
            tools=openai_tools,
            tool_choice="auto",
        )
        choice = response.choices[0].message
        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": choice.content or "",
        }
        if choice.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments or "{}",
                    },
                }
                for tc in choice.tool_calls
            ]
        messages.append(assistant_msg)

        if not choice.tool_calls:
            print(choice.content or "(no content)")
            return

        for tc in choice.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            print(f"  → call_tool({name!r}, toolset={pin.name}@{pin.version})")
            try:
                result = await client.call_tool(name, args, toolset=pin)
                body = _text_from_result(result)
            except Exception as exc:
                body = f"ERROR: {exc}"
                print(f"  ← {body}")
            else:
                print(f"  ← {body}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": body,
                }
            )

    print("(stopped after max tool rounds)", file=sys.stderr)


def main() -> None:
    try:
        anyio.run(_run)
    except Exception as exc:
        print(f"agent ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
