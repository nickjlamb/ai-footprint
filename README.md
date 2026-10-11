# AI Footprint

**How much water and energy does AI use? An MCP server and JSON API that answers with the boundary, assumptions and sources attached.**

[![ci](https://github.com/nickjlamb/ai-footprint/actions/workflows/ci.yml/badge.svg)](https://github.com/nickjlamb/ai-footprint/actions/workflows/ci.yml)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-io.github.nickjlamb%2Fai--footprint-6E56CF)](https://registry.modelcontextprotocol.io/?q=ai-footprint)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

The server behind the [PharmaTools.AI AI Water & Energy Calculator](https://www.pharmatools.ai/water-consumption-calculator), exposed as tools an AI agent can call. Published per-prompt estimates of AI water use range from 0.3 mL to 50 mL. Most of that spread is explainable: when the figure was measured, where the accounting boundary is drawn, what kind of workload is counted, and whose data centre it is. Every result from this server says which boundary it uses, which assumptions it made and which methodology version it comes from, so a figure can be checked rather than repeated.

- **No model in any tool.** It's arithmetic over a published methodology. Same input, same answer.
- **No API key, no install.** A hosted, read-only, rate-limited endpoint.
- **Identical to the calculator page.** The test suite pins the server's outputs to the page's.

## Quick start

Hosted endpoint (streamable HTTP):

```
https://prompt-tightener-production.up.railway.app/mcp
```

**Claude Code**

```bash
claude mcp add --transport http ai-footprint https://prompt-tightener-production.up.railway.app/mcp
```

**Claude Desktop / claude.ai:** Settings → Connectors → Add custom connector, then paste the URL.

**Cursor** (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "ai-footprint": { "url": "https://prompt-tightener-production.up.railway.app/mcp" }
  }
}
```

Then ask: *"How much water does 30 ChatGPT prompts a day use over a working year?"* or *"Estimate the footprint of this coding session: 200k input tokens, 3M cached, 40k output."*

## Tools

| Tool | What it does |
|---|---|
| `estimate_ai_footprint` | Queries per day × usage tier (`simple` ~0.34 Wh, `mixed` ~1 Wh, `intensive` ~3 Wh per prompt) × boundary × days → energy, water, everyday equivalents, assumptions. |
| `get_methodology` | Per-prompt figures, both boundaries, sources, limitations, a citation line, and why published estimates differ by ~100×. Call this before explaining any AI water figure. |
| `compare_water_use` | Any volume in mL → teaspoons, 500 mL bottles, shower time, lifecycle items (A4 sheet, almond, tea, burger), with the caveat that lifecycle footprints are a much wider boundary. |
| `estimate_session_footprint` | Token counts for an agent or coding session (input, output incl. reasoning, cache reads) → central estimate and a 0.3–3× range. |

All four are annotated read-only and idempotent.

## Methodology

Energy first, water derived from it.

- **Energy per prompt:** OpenAI cites ~0.34 Wh per ChatGPT query; Google reports a median Gemini text prompt at 0.24 Wh (2025). Image generation and long reasoning run to ~3 Wh or more.
- **Water per Wh:**
  - `onsite` (~1.0 mL/Wh): data-centre cooling only, as implied by Google's disclosure (0.26 mL per 0.24 Wh prompt). The highest of the published provider figures (Amazon 0.12 L/kWh, Microsoft 0.27, Google ~1.08) is used.
  - `comprehensive` (~4.1 mL/Wh): adds ~3.1 mL/Wh for water consumed generating the electricity (US grid average, Li et al.).
- **Typical text prompt:** ~0.34 mL onsite, ~1.4 mL comprehensive. The widely quoted 2023 figures (~40–500 mL) describe hardware that no longer exists.

**Session estimates** are calibrated so ~1,000 input + ~400 output tokens on a frontier model equals one typical prompt (0.34 Wh), with output tokens costing ~5× input and cache reads ~0.1×. These are assumptions, not measurements, so the tool returns a range and says so.

Limitations: vendor figures aren't peer-reviewed, describe median prompts and exclude training; electricity water uses US grid averages. Results are indicative estimates.

Sources: [Google (2025)](https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference/) · [OpenAI per-query figures](https://www.datacenterdynamics.com/en/news/sam-altman-chatgpt-queries-consume-034-watt-hours-of-electricity-and-0000085-gallons-of-water/) · [Li et al., *Making AI Less Thirsty*](https://arxiv.org/abs/2304.03271) · [MIT Technology Review (2025)](https://www.technologyreview.com/2025/08/21/1122288/google-gemini-ai-energy/) · [Water Footprint Network](https://www.waterfootprint.org/resources/interactive-tools/product-gallery/)

The full write-up is on the [calculator page](https://www.pharmatools.ai/water-consumption-calculator). When the methodology is revised, `server/footprint.py` is updated and `METHODOLOGY_VERSION` bumped.

## JSON API

The same tools as plain GET endpoints, with open CORS:

```bash
B=https://prompt-tightener-production.up.railway.app
curl "$B/api/footprint?queries_per_day=25&days=250"
curl "$B/api/methodology"
curl "$B/api/compare?water_ml=500"
curl "$B/api/session?input_tokens=200000&output_tokens=40000&cached_input_tokens=3000000"
```

Public routes are limited to 120 requests per minute per client. Usage is logged as tool or endpoint names only. Inputs and IP addresses are not logged.

## Also in this repo: the prompt tightener

`POST /tighten` powers the "Make your first prompt the only one" tool on the calculator page. It sends a draft prompt to Claude Haiku, which rewrites it to get a usable answer first time. Gaps are filled with `[placeholders]` rather than invented facts. The page then shows what the rewrite itself cost in water against the follow-ups it should save. Unlike the footprint tools, it calls a model, so it's locked down: pharmatools.ai-only CORS, a 1,500-character input cap, per-IP and daily caps, forced tool output, and no prompt logging. The page embed is in [`web/prompt-tightener-embed.html`](web/prompt-tightener-embed.html).

## Run it yourself

```bash
cd server
pip install -r requirements.txt
MOCK=1 uvicorn main:app --port 8000          # MOCK=1: the tightener returns a canned rewrite, no key needed
# MCP at http://localhost:8000/mcp, JSON API at http://localhost:8000/api
```

To run the tightener for real, set `ANTHROPIC_API_KEY`. Optional settings: `MODEL` (default `claude-haiku-4-5`), `ALLOWED_ORIGINS`, `PER_IP_PER_MIN`, `PER_IP_PER_DAY`, `GLOBAL_PER_DAY`, `MAX_INPUT_CHARS` and `PUBLIC_PER_IP_PER_MIN`. The rate limits are in-memory, so they assume a single instance.

## Tests

```bash
cd server
pip install -r requirements.txt -r requirements-dev.txt
MOCK=1 python -m pytest -q
```

The tests pin the server to the calculator page (25 prompts a day = 8.5 Wh and 34.8 mL; 250 days = 2.1 kWh and 8.7 L). They also check the session calibration, input validation, open CORS on the public routes and strict CORS on `/tighten`.

## Layout

```
server/
  footprint.py      constants, methodology and arithmetic (single source of truth)
  mcp_tools.py      the four MCP tools (FastMCP, streamable HTTP)
  main.py           FastAPI app: /mcp, /api/*, /tighten, CORS and rate limits
  test_footprint.py
web/
  prompt-tightener-embed.html
server.json         MCP Registry entry
```

## License

[MIT](LICENSE) © [PharmaTools.AI](https://www.pharmatools.ai)
