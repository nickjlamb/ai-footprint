"""Call every AI Footprint tool over MCP (streamable HTTP) with the official Python SDK.

    pip install "mcp>=1.12,<2"
    python examples/mcp_client.py                      # hosted endpoint
    python examples/mcp_client.py http://localhost:8000/mcp
"""
import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = sys.argv[1] if len(sys.argv) > 1 else "https://prompt-tightener-production.up.railway.app/mcp"

CALLS = [
    ("estimate_ai_footprint", {"queries_per_day": 30, "days": 250}),
    ("estimate_session_footprint",
     {"input_tokens": 200_000, "output_tokens": 40_000, "cached_input_tokens": 3_000_000}),
    ("compare_water_use", {"water_ml": 500}),
    ("get_methodology", {}),
]


def summarise(name: str, d: dict) -> str:
    if name == "estimate_ai_footprint":
        t = d["total"]
        return f"{t['energy']}, {t['water']} over {d['inputs']['days']} days ({t['energy_equivalents']['tv_100w']})"
    if name == "estimate_session_footprint":
        c = d["central"]
        return f"{c['energy']}, {c['water']} (range {d['range']['water']}), about {d['equivalent_chat_prompts']} chat prompts"
    if name == "compare_water_use":
        return f"{d['water']} = {d['everyday']['teaspoons']} teaspoons, {d['everyday']['shower']}"
    return d["summary"][:110] + "..."


async def main() -> None:
    async with streamablehttp_client(URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            info = await session.initialize()
            tools = await session.list_tools()
            print(f"Connected to {info.serverInfo.name}: {', '.join(t.name for t in tools.tools)}\n")

            for name, args in CALLS:
                result = await session.call_tool(name, args)
                data = result.structuredContent or json.loads(result.content[0].text)
                data = data.get("result", data)  # FastMCP wraps dict returns
                print(f"{name}({json.dumps(args)})")
                print("   " + summarise(name, data) + "\n")

if __name__ == "__main__":
    asyncio.run(main())
