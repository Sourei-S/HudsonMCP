from __future__ import annotations
import argparse
import asyncio
import json
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from hudson_mcp.config import set_config_dir
from hudson_mcp.tools import TOOLS

server = Server("hudson-mcp")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(name=name, description=spec["description"], inputSchema=spec["schema"])
        for name, spec in TOOLS.items()
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    spec = TOOLS.get(name)
    if spec is None:
        raise ValueError(f"unknown tool: {name}")
    try:
        result = spec["fn"](arguments or {})
    except Exception as e:
        result = {"error": "tool execution failed", "tool": name, "type": type(e).__name__}
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def _run() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hudson-mcp",
        description="Post-incident recovery decision engine for Claude Code",
    )
    parser.add_argument(
        "--config",
        default=None,
        metavar="DIR",
        help="Custom YAML config directory. Files found here override bundled defaults.",
    )
    args = parser.parse_args()
    set_config_dir(args.config)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
