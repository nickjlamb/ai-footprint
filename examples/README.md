# Examples

Every example runs against the hosted endpoint as is. Set `AI_FOOTPRINT_URL` (or pass a URL to the Python client) to point any of them at a local server.

| File | What it shows | Run it |
|---|---|---|
| [`mcp_client.py`](mcp_client.py) | Connect over MCP with the official Python SDK, list the tools and call all four | `pip install "mcp>=1.12,<2" && python examples/mcp_client.py` |
| [`api.mjs`](api.mjs) | The JSON API from Node or a browser, no dependencies | `node examples/api.mjs` |
| [`curl.sh`](curl.sh) | One `curl` per endpoint | `bash examples/curl.sh` |
| [`outputs/`](outputs) | Full responses from each tool, captured from the live server | |

## Prompts to try in an MCP client

Once the server is connected, ask in plain language. The model chooses the tool.

| Ask | Tool the model calls | What comes back |
|---|---|---|
| *How much water does ChatGPT use per prompt?* | `get_methodology` | ~0.34 mL onsite, ~1.4 mL including electricity generation, and why other published figures run from 0.3 mL to 50 mL |
| *How much water do 30 prompts a day use over a working year?* | `estimate_ai_footprint` | 2.6 kWh and 10.5 L over 250 days, with assumptions |
| *Estimate this coding session: 200k input tokens, 3M cached, 40k output.* | `estimate_session_footprint` | 79.3 Wh and 325 mL, with a range of 97.6 mL to 976 mL |
| *Is 500 mL a lot?* | `compare_water_use` | 102 teaspoons, 3 seconds of a shower, or 0.042 of one almond's lifecycle footprint, with the boundary caveat |
| *I read that 20 to 50 ChatGPT questions use a 500 mL bottle of water. Is that still true?* | `get_methodology` | Why that 2023 estimate describes hardware that no longer exists, and what current disclosures say instead |

## Example output

`estimate_ai_footprint(queries_per_day=30, days=250)`, trimmed. Full response in [`outputs/estimate_ai_footprint.json`](outputs/estimate_ai_footprint.json).

```json
{
  "per_query": { "energy_wh": 0.34, "water_ml": 1.39 },
  "total": {
    "energy": "2.6 kWh",
    "water": "10.5 L",
    "energy_equivalents": { "tv_100w": "25.5 hrs of TV", "phone_charges": "170 phone charges" },
    "water_equivalents": { "bottles_500ml": 20.91, "shower": "1.2 min of showering" }
  },
  "assumptions": [
    "Usage tier: Simple text – chat, search, summaries (0.34 Wh per prompt).",
    "Boundary: Onsite cooling plus water consumed generating the electricity (~4.1 mL/Wh; US grid average per Li et al.).",
    "..."
  ],
  "methodology_version": "2026-09",
  "source": "https://www.pharmatools.ai/water-consumption-calculator"
}
```

## Where to find token counts for a session

`estimate_session_footprint` wants the **sum** of tokens across every model call. Agent loops resend the context on every turn, so this sum is usually far larger than the conversation looks.

- **Claude API:** add up `usage.input_tokens`, `usage.output_tokens` and `usage.cache_read_input_tokens` across the responses.
- **OpenAI API:** `usage.prompt_tokens` (minus `prompt_tokens_details.cached_tokens`), `usage.completion_tokens`, and the cached tokens separately.
- **Coding agents:** most show session usage in a cost or usage command. Use the totals it reports.
