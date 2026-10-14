# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

Two version numbers matter:

- **Release version** (`1.0.0`): the server, its tools and the JSON API. A breaking change to a tool's inputs or outputs is a major version.
- **Methodology version** (`2026-10`): the figures and sources. Every response carries it. A methodology change is always noted here, even when the release is a patch.

## [Unreleased]

### Added

- Embeddable widget for other sites. `GET /widget` is the calculator as a small page any site can put in an iframe (`frame-ancestors *`), and `GET /widget.js` is a one-line embed that replaces its own script tag with that iframe and keeps its height in step. Options as `data-` attributes or query parameters: `theme` (light, dark, auto), `accent` (hex colour), `prompts` (1–200), `mix` (text, mixed, intensive) and `basis` (comprehensive, onsite). The figures are injected from `footprint.py`, so the widget always matches the API and the page. Everything is computed in the visitor's browser: no API calls, cookies or tracking.

### Methodology

- `2026-10`: figures unchanged. Every estimate now carries a likely range of 0.3x to 3x the central figure: `estimate_ai_footprint` gains a `range` for the total, matching the session tool, and `get_methodology` gains an `uncertainty` block with the evidence behind the band. The 3 Wh intensive tier is now sourced to benchmark data (Jegham et al. 2025) rather than a news analysis, and Epoch AI's GPT-4o estimate is listed; the figure is unchanged. The method is written up as a versioned note on Zenodo; responses link it as `method_note` once the DOI is set (`METHOD_NOTE_DOI`), and `how_to_cite` then cites it.

### Added

- `POST /read-claim` for the calculator page's headline checker. When the page can't read a pasted claim itself, and the visitor chooses to, it sends the claim here. Claude Haiku returns only what the claim states (amount, unit, what it's per, year, boundary) through a forced tool call, and the server checks those fields before returning them. The page then explains the claim using fixed rules, so the model never writes the verdict. It has the same protections as `/tighten`: pharmatools.ai-only CORS, per-IP and daily caps (shared with the tightener), a 400-character cap and no logging of the text.

## [1.0.4] - 2026-10-13

### Security

- Rate limiting reads the client address from the position Railway's edge writes it in `X-Forwarded-For` and ignores entries further left, which a caller can set to anything. Forging the header no longer risks getting round the limits on other hosts. `PROXY_ENTRIES` sets how many proxy-added entries to skip.
- The `/tighten` rate-limit maps are now capped in size, like the public limiter's.
- Runtime dependencies are pinned to exact versions, including `mcp` 1.30.0, which carries the SDK's published security fixes. Test-only packages have moved out of `requirements.txt`. Dependabot keeps the pins current.

## [1.0.3] - 2026-10-13

### Fixed

- Each tool's title is now also set in `annotations.title`, where Claude's Connectors Directory looks for it. A test checks every tool has a title and read-only annotations.

## [1.0.2] - 2026-10-13

### Changed

- Opening the bare domain in a browser now redirects to the documentation instead of returning Not found. Set `DOCS_URL` to change where it points.
- The release workflow no longer fails when a release for the tag already exists.

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

[Unreleased]: https://github.com/nickjlamb/ai-footprint/compare/v1.0.4...HEAD
[1.0.4]: https://github.com/nickjlamb/ai-footprint/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/nickjlamb/ai-footprint/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/nickjlamb/ai-footprint/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/nickjlamb/ai-footprint/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/nickjlamb/ai-footprint/releases/tag/v1.0.0
