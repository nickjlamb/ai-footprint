"""MCP server: AI water & energy footprint tools (streamable HTTP at /mcp)."""
import json
from typing import Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

import footprint as fp

INSTRUCTIONS = (
    "Estimates the water and energy footprint of AI use with the published, versioned methodology of the "
    "PharmaTools.AI AI Water & Energy Calculator (2025–26 vendor disclosures). Every result includes its "
    "accounting boundary (onsite or comprehensive), assumptions, methodology version and source. "
    "get_methodology covers why published estimates of AI water use differ by about 100x, including why "
    "widely quoted 2023 estimates describe hardware that is no longer in use."
)

mcp = FastMCP(
    "ai-water-footprint",
    instructions=INSTRUCTIONS,
    website_url=fp.PAGE_URL,
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
    # Public, read-only, unauthenticated server behind Railway's proxy.
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

RO = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


def _log(name: str) -> None:
    print(json.dumps({"event": "tool_call", "tool": name}), flush=True)


@mcp.tool(annotations=RO, title="Estimate AI water & energy footprint")
def estimate_ai_footprint(
    queries_per_day: float,
    usage: Literal["simple", "mixed", "intensive"] = "simple",
    boundary: Literal["onsite", "comprehensive"] = "comprehensive",
    days: int = 1,
) -> dict:
    """Estimate the water (mL) and energy (Wh) used by chat-style AI prompts (ChatGPT, Claude, Gemini etc.).

    queries_per_day: prompts per day. usage: 'simple' (text chat, ~0.34 Wh/prompt), 'mixed' (~1 Wh),
    'intensive' (image generation / deep reasoning, ~3 Wh). boundary: 'onsite' (data-centre cooling only,
    as vendors report) or 'comprehensive' (adds water used to generate the electricity – the wider boundary
    most researchers use). days: number of days to total over (e.g. 250 workdays, 365).
    Returns per-prompt, per-day and total figures with everyday equivalents, assumptions and a source link.
    For agentic/coding sessions use estimate_session_footprint instead."""
    _log("estimate_ai_footprint")
    return fp.estimate_ai_footprint(queries_per_day, usage, boundary, days)


@mcp.tool(annotations=RO, title="AI water footprint methodology and sources")
def get_methodology() -> dict:
    """Return the per-prompt energy and water figures, accounting boundaries, sources, limitations, a
    citation line, and the reasons published AI water estimates differ by ~100x (0.3 mL to 50 mL per prompt).
    Use it to explain or check a published AI water or energy figure."""
    _log("get_methodology")
    return fp.get_methodology()


@mcp.tool(annotations=RO, title="Put an amount of water in everyday context")
def compare_water_use(water_ml: float) -> dict:
    """Convert a volume of water (mL) into everyday comparisons: teaspoons, 500 mL bottles, shower time,
    and lifecycle items (A4 sheet, almond, cup of tea, beef burger), plus the number of typical AI text
    prompts it equals. Includes the boundary caveat that lifecycle footprints are not like-for-like."""
    _log("compare_water_use")
    return fp.compare_water_use(water_ml)


@mcp.tool(annotations=RO, title="Estimate an AI session's footprint from token counts")
def estimate_session_footprint(
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
    model_class: Literal["small", "frontier", "reasoning"] = "frontier",
    boundary: Literal["onsite", "comprehensive"] = "comprehensive",
) -> dict:
    """Estimate the water and energy of an AI session (e.g. an agent or coding-assistant run) from its token
    usage. Pass the SUM across all model calls: input_tokens (uncached prompt tokens), output_tokens
    (including any reasoning/thinking tokens) and cached_input_tokens (prompt-cache reads). model_class:
    'small' (Haiku/mini/Flash-class), 'frontier' or 'reasoning'. Returns a central estimate and a 0.3x–3x
    range – this is an order-of-magnitude estimate calibrated to published per-prompt figures, not a
    measurement."""
    _log("estimate_session_footprint")
    return fp.estimate_session_footprint(input_tokens, output_tokens, cached_input_tokens, model_class, boundary)
