# Contributing to AI Footprint

Thanks for helping. The most valuable contributions here are often not code: a better source, a newer disclosure, or a case where an answer misleads.

By taking part you agree to follow the [code of conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

| You have | Do this |
|---|---|
| A newer or better source for a figure | Open a [methodology issue](https://github.com/nickjlamb/ai-footprint/issues/new?template=methodology.yml) with the link and the figure |
| A wrong, confusing or misleading answer | Open a [bug report](https://github.com/nickjlamb/ai-footprint/issues/new?template=bug.yml) with the tool call and the response |
| An idea for a tool or parameter | Open a [feature request](https://github.com/nickjlamb/ai-footprint/issues/new?template=feature.yml), or check the [roadmap](ROADMAP.md) first |
| A security problem | Don't open an issue. Follow [SECURITY.md](SECURITY.md) |
| A fix you've already written | Open a pull request. For anything bigger than a small fix, open an issue first so we can agree the approach |

## Development setup

You need Python 3.10 or later.

```bash
git clone https://github.com/nickjlamb/ai-footprint && cd ai-footprint
python -m venv .venv && source .venv/bin/activate
pip install -r server/requirements.txt -r server/requirements-dev.txt

cd server
MOCK=1 python -m pytest -q                     # tests
ruff check ..                                  # lint
MOCK=1 uvicorn main:app --port 8000 --reload   # run locally
python ../examples/mcp_client.py http://localhost:8000/mcp   # drive it over MCP
```

`MOCK=1` stubs the prompt tightener, so you don't need an Anthropic API key. The footprint tools never need one.

## How the code is organised

- [`server/footprint.py`](server/footprint.py) is the single source of truth: constants, sources and every calculation. Put logic here.
- [`server/mcp_tools.py`](server/mcp_tools.py) and the `/api/*` routes in [`server/main.py`](server/main.py) are thin wrappers. They validate types and call `footprint.py`. Keep them thin, so the MCP tools and the JSON API can't drift apart.
- Tool docstrings are what the model reads when it decides which tool to call. Treat changes to them as changes to behaviour: keep them precise, and say what the tool is not for.

## Changing the methodology

The figures are published on the [calculator page](https://www.pharmatools.ai/water-consumption-calculator) and quoted elsewhere, so changes follow a short process:

1. **Open a methodology issue first** with the source, the figure, and what it would replace.
2. **Prefer primary sources**: a provider's own disclosure or a peer-reviewed paper over a news article about it. Say what boundary the source uses.
3. **When the change is agreed**, update the constants and `SOURCES` in `footprint.py`, bump `METHODOLOGY_VERSION` (format `YYYY-MM`) and `REVIEWED`, and update the parity tests in `test_footprint.py`.
4. **Record it in [CHANGELOG.md](CHANGELOG.md)** under a `### Methodology` heading.
5. The calculator page is updated in step by the maintainer. A methodology change isn't released until both match.

## Pull requests

- Keep each pull request to one change.
- Add or update tests for any behaviour change. CI runs lint, the tests on Python 3.10 to 3.13, and an end-to-end MCP check.
- Add a line under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) for anything a user would notice.
- Don't add a model call to a footprint tool. Determinism is the point.
- Don't log tool inputs, prompts or IP addresses.

## Releases

Maintainers release by moving the `Unreleased` entries under a new version heading in `CHANGELOG.md`, setting the same version in `server.json`, and pushing a tag:

```bash
git tag v1.1.0 && git push origin v1.1.0
```

The [release workflow](.github/workflows/release.yml) checks that the tag, `server.json` and the changelog agree, runs the tests, and publishes a GitHub release with that version's changelog section as its notes. If the version changed, update the MCP Registry entry with `mcp-publisher publish`.
