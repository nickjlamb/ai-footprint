# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

Two version numbers matter:

- **Release version** (`1.0.0`): the server, its tools and the JSON API. A breaking change to a tool's inputs or outputs is a major version.
- **Methodology version** (`2026-09`): the figures and sources. Every response carries it. A methodology change is always noted here, even when the release is a patch.

## [Unreleased]

## [1.0.1] - 2026-10-13

### Changed

- Hosted endpoint moved to `https://footprint.pharmatools.ai/mcp`. The previous Railway address keeps working.
- Server instructions and the `get_methodology` description now describe what the tools return, rather than telling the model how to quote results.
- Privacy section added to the README, covering what the hosted server logs and keeps.

## [1.0.0] - 2026-10-11

First public release.

### Added

- MCP server over streamable HTTP at `/mcp`, with four read-only tools:
  - `estimate_ai_footprint`: energy and water for chat-style prompts over any number of days, by usage tier and boundary.
  - `estimate_session_footprint`: an agent or coding session from its token counts, with a 0.3–3× range.
  - `compare_water_use`: any volume of water in everyday and lifecycle terms, with the boundary caveat.
  - `get_methodology`: figures, boundaries, sources, limitations, a citation line and why published estimates differ ~100×.
- JSON API mirroring the tools: `/api/footprint`, `/api/session`, `/api/compare`, `/api/methodology`, with open CORS.
- Hosted endpoint, listed in the official MCP Registry as `io.github.nickjlamb/ai-footprint`.
- Prompt tightener endpoint (`POST /tighten`) and its calculator-page embed.
- Per-path CORS and rate limiting: open for the footprint routes, pharmatools.ai-only with daily caps for `/tighten`.
- `/health` endpoint, answering `GET` and `HEAD` for uptime monitors.
- Test suite pinning outputs to the calculator page (25 prompts a day = 8.5 Wh and 34.8 mL).
- Examples: Python MCP client, JavaScript and `curl` clients, captured responses.
- Project documentation: contributing guide, security policy, code of conduct, roadmap, citation file, issue and pull request templates.
- CI on Python 3.10 to 3.13 with lint, tests and an end-to-end MCP check. Tagged releases are published automatically from this changelog.

### Methodology

- `2026-09`: energy per prompt from 2025 vendor disclosures (0.34 Wh simple, 1 Wh mixed, 3 Wh intensive); water at ~1.0 mL/Wh onsite and ~4.1 mL/Wh comprehensive. Typical text prompt ~0.34 mL onsite, ~1.4 mL comprehensive.

[Unreleased]: https://github.com/nickjlamb/ai-footprint/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/nickjlamb/ai-footprint/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/nickjlamb/ai-footprint/releases/tag/v1.0.0
