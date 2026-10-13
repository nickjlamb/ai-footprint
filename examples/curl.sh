#!/usr/bin/env bash
# The JSON API from the shell. Every endpoint is a plain GET with open CORS.
set -euo pipefail
B="${AI_FOOTPRINT_URL:-https://footprint.pharmatools.ai}"

# 30 text prompts a day over a 250-day working year
curl -s "$B/api/footprint?queries_per_day=30&days=250"

# An agent session from its token counts (sum across every model call)
curl -s "$B/api/session?input_tokens=200000&output_tokens=40000&cached_input_tokens=3000000"

# Put a volume of water in context
curl -s "$B/api/compare?water_ml=500"

# Figures, boundaries, sources and why published estimates differ ~100x
curl -s "$B/api/methodology"
