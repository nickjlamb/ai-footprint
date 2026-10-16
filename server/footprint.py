"""
AI water & energy footprint engine – the same arithmetic as
https://www.pharmatools.ai/water-consumption-calculator

Single source of truth for the agent tools (MCP + JSON API). If the page's
methodology is revised, update the constants here and bump METHODOLOGY_VERSION.
"""
from __future__ import annotations

PAGE_URL = "https://www.pharmatools.ai/water-consumption-calculator"
METHODOLOGY_VERSION = "2026-10"
REVIEWED = "October 2026"
# Method note (Zenodo preprint) for this methodology version. Empty until the DOI is minted.
METHOD_NOTE_DOI = "10.5281/zenodo.23417340"

# Energy per chat-style prompt, Wh (matches the page's ENERGY_PER_QUERY)
ENERGY_PER_QUERY_WH = {"simple": 0.34, "mixed": 1.0, "intensive": 3.0}
USAGE_LABELS = {
    "simple": "Simple text – chat, search, summaries",
    "mixed": "Mixed – text plus some images and reasoning",
    "intensive": "Intensive – image generation, deep reasoning",
}

# Water per Wh, mL (matches the page's WATER_PER_WH)
WATER_PER_WH_ML = {"onsite": 1.0, "comprehensive": 4.1}
BOUNDARY_LABELS = {
    "onsite": "Vendor-reported, onsite data-centre cooling only (~1 mL/Wh, implied by Google's 2025 disclosure)",
    "comprehensive": "Onsite cooling plus water consumed generating the electricity (~4.1 mL/Wh; US grid average per Li et al.)",
}

SOURCES = [
    {"name": "Google (2025), Measuring the environmental impact of AI inference",
     "url": "https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference/",
     "used_for": "Median Gemini text prompt 0.24 Wh; onsite water 0.26 mL per prompt (~1.08 mL/Wh)"},
    {"name": "OpenAI per-query figures (2025), via DatacenterDynamics",
     "url": "https://www.datacenterdynamics.com/en/news/sam-altman-chatgpt-queries-consume-034-watt-hours-of-electricity-and-0000085-gallons-of-water/",
     "used_for": "~0.34 Wh per ChatGPT query – the 'simple' tier"},
    {"name": "Li et al., Making AI Less Thirsty",
     "url": "https://arxiv.org/abs/2304.03271",
     "used_for": "~3.1 mL/Wh for water consumed in electricity generation (US grid average)"},
    {"name": "Jegham et al. (2025), How Hungry is AI? Benchmarking energy, water, and carbon footprint of LLM inference",
     "url": "https://arxiv.org/abs/2505.09598",
     "used_for": "Reasoning queries at ~1–12 Wh (o3: 1.2 Wh short, 12.2 Wh long) – the 3 Wh 'intensive' tier; 0.42 Wh short GPT-4o prompt"},
    {"name": "Epoch AI (2025), How much energy does ChatGPT use?",
     "url": "https://epoch.ai/gradient-updates/how-much-energy-does-chatgpt-use",
     "used_for": "~0.3 Wh per typical GPT-4o query – part of the evidence for the likely range"},
    {"name": "Water Footprint Network product gallery",
     "url": "https://www.waterfootprint.org/resources/interactive-tools/product-gallery/",
     "used_for": "Lifecycle 'virtual water' comparisons (paper, tea, burger)"},
]

# Everyday comparisons (same factors as the page)
TV_WATTS = 100
PHONE_CHARGE_WH = 15
SHOWER_ML_PER_MIN = 9000
BOTTLE_ML = 500
TEASPOON_ML = 4.9
LIFECYCLE_ITEMS = [  # (label, mL) – full lifecycle footprints, a WIDER boundary than AI operational water
    ("sheet of A4 paper (lifecycle)", 10_000),
    ("California almond (total footprint)", 12_000),
    ("cup of tea (lifecycle)", 30_000),
    ("beef burger (lifecycle)", 2_400_000),
]

# --- per-token model (session tool) ------------------------------------------
# Calibrated so a typical chat prompt (~1,000 input + ~400 output tokens on a
# frontier model) costs the page's 0.34 Wh. Output tokens are assumed ~5x the
# energy of input tokens (decode vs prefill); cache reads ~0.1x input.
# These are assumptions, not measurements – results are returned as a range.
CALIB_INPUT, CALIB_OUTPUT, OUTPUT_TO_INPUT, CACHE_TO_INPUT = 1000, 400, 5.0, 0.1
WH_PER_INPUT_TOKEN = ENERGY_PER_QUERY_WH["simple"] / (CALIB_INPUT + OUTPUT_TO_INPUT * CALIB_OUTPUT)
MODEL_CLASS_FACTOR = {"small": 0.3, "frontier": 1.0, "reasoning": 1.0}
RANGE_LOW, RANGE_HIGH = 0.3, 3.0  # likely range applied to every central estimate (methodology 2026-10)
RANGE_NOTE = (f"Likely range {RANGE_LOW:g}x–{RANGE_HIGH:g}x the central estimate: a judgement-based summary of how much "
              "published per-prompt energy figures and provider/grid water intensities vary, not a statistical interval.")

MAX_QUERIES = 10_000_000
MAX_DAYS = 3650
MAX_TOKENS = 10_000_000_000


class InputError(ValueError):
    pass


def _r(x: float, nd: int = 2) -> float:
    return float(f"{x:.{nd}g}") if x < 1 else round(x, nd)


def fmt_energy(wh: float) -> str:
    if wh >= 1_000_000:
        return f"{wh / 1_000_000:.1f} MWh".replace(".0 ", " ")
    if wh >= 1000:
        return f"{wh / 1000:.1f} kWh".replace(".0 ", " ")
    if wh >= 100:
        return f"{round(wh)} Wh"
    return f"{wh:.1f} Wh".replace(".0 ", " ")


def fmt_water(ml: float) -> str:
    if ml >= 1_000_000:
        return f"{ml / 1_000_000:.1f} m³".replace(".0 ", " ")
    if ml >= 1000:
        return f"{ml / 1000:.1f} L".replace(".0 ", " ")
    if ml >= 100:
        return f"{round(ml)} mL"
    return f"{ml:.1f} mL".replace(".0 ", " ")


def _duration(minutes: float, what: str) -> str:
    if minutes < 1:
        return f"{round(minutes * 60)} sec of {what}"
    if minutes < 60:
        return f"{minutes:.1f}".rstrip("0").rstrip(".") + f" min of {what}"
    return f"{minutes / 60:.1f}".rstrip("0").rstrip(".") + f" hrs of {what}"


def energy_equivalents(wh: float) -> dict:
    charges = wh / PHONE_CHARGE_WH
    return {
        "tv_100w": _duration(wh * 60 / TV_WATTS, "TV"),
        "phone_charges": f"{round(charges * 100)}% of a phone charge" if charges < 1
        else f"{charges:.1f}".rstrip("0").rstrip(".") + " phone charges",
    }


def water_equivalents(ml: float) -> dict:
    return {
        "teaspoons": round(ml / TEASPOON_ML, 1),
        "bottles_500ml": round(ml / BOTTLE_ML, 2),
        "shower": _duration(ml / SHOWER_ML_PER_MIN, "showering"),
    }


def _check_choice(value: str, options: dict, name: str) -> str:
    v = (value or "").strip().lower()
    aliases = {"text": "simple", "reported": "onsite", "vendor": "onsite", "vendor-reported": "onsite"}
    v = aliases.get(v, v)
    if v not in options:
        raise InputError(f"{name} must be one of: {', '.join(options)}")
    return v


def estimate_ai_footprint(queries_per_day: float, usage: str = "simple",
                          boundary: str = "comprehensive", days: int = 1) -> dict:
    usage = _check_choice(usage, ENERGY_PER_QUERY_WH, "usage")
    boundary = _check_choice(boundary, WATER_PER_WH_ML, "boundary")
    if not (0 < queries_per_day <= MAX_QUERIES):
        raise InputError(f"queries_per_day must be between 0 and {MAX_QUERIES:,}")
    if not (1 <= days <= MAX_DAYS):
        raise InputError(f"days must be between 1 and {MAX_DAYS}")
    per_wh = ENERGY_PER_QUERY_WH[usage]
    per_ml = per_wh * WATER_PER_WH_ML[boundary]
    day_wh, day_ml = queries_per_day * per_wh, queries_per_day * per_ml
    tot_wh, tot_ml = day_wh * days, day_ml * days
    return {
        "inputs": {"queries_per_day": queries_per_day, "usage": usage, "boundary": boundary, "days": days},
        "per_query": {"energy_wh": per_wh, "water_ml": round(per_ml, 2)},
        "per_day": {"energy_wh": round(day_wh, 2), "water_ml": round(day_ml, 1),
                    "energy": fmt_energy(day_wh), "water": fmt_water(day_ml)},
        "range": {"energy_wh": [_r(tot_wh * RANGE_LOW, 3), _r(tot_wh * RANGE_HIGH, 3)],
                  "water_ml": [_r(tot_ml * RANGE_LOW, 3), _r(tot_ml * RANGE_HIGH, 3)],
                  "water": f"{fmt_water(tot_ml * RANGE_LOW)} – {fmt_water(tot_ml * RANGE_HIGH)}",
                  "applies_to": "total"},
        "total": {"energy_wh": round(tot_wh, 2), "water_ml": round(tot_ml, 1),
                  "energy": fmt_energy(tot_wh), "water": fmt_water(tot_ml),
                  "energy_equivalents": energy_equivalents(tot_wh),
                  "water_equivalents": water_equivalents(tot_ml)},
        "assumptions": [
            f"Usage tier: {USAGE_LABELS[usage]} ({per_wh} Wh per prompt).",
            f"Boundary: {BOUNDARY_LABELS[boundary]}.",
            "Chat-style prompts (one prompt, one response). Agentic sessions can be far higher – use estimate_session_footprint.",
            "Uses the most conservative (highest) of the published onsite water intensities. Excludes model training.",
            RANGE_NOTE,
        ],
        **_meta(),
    }


def get_methodology() -> dict:
    return {
        "summary": ("Energy first, water derived from it. Per-prompt energy comes from 2025 vendor disclosures "
                    "(OpenAI ~0.34 Wh, Google median 0.24 Wh for text); water = energy x water intensity. "
                    "'onsite' counts data-centre cooling only; 'comprehensive' adds the water consumed "
                    "generating the electricity."),
        "energy_per_query_wh": ENERGY_PER_QUERY_WH,
        "usage_tiers": USAGE_LABELS,
        "water_per_wh_ml": WATER_PER_WH_ML,
        "boundaries": BOUNDARY_LABELS,
        "typical_text_prompt": {
            "onsite_ml": round(ENERGY_PER_QUERY_WH["simple"] * WATER_PER_WH_ML["onsite"], 2),
            "comprehensive_ml": round(ENERGY_PER_QUERY_WH["simple"] * WATER_PER_WH_ML["comprehensive"], 2),
            "2023_research_estimate_ml": 40,
        },
        "why_estimates_vary_100x": [
            "When it was measured: Google reports a 33x drop in energy per prompt in twelve months; 2023 estimates (~40 mL/prompt) describe hardware that no longer exists.",
            "Where the line is drawn: onsite cooling only vs including water used to generate the electricity gives figures several times apart. Neither is wrong; a figure that does not say which cannot be checked.",
            "What is measured: chat prompts vs agentic tasks, which reprocess a growing context over dozens of calls and can exceed per-prompt figures by orders of magnitude.",
            "Whose data centre: onsite water intensity differs ~9x between providers – 0.12 L/kWh (Amazon), 0.27 (Microsoft), ~1.08 implied by Google. This methodology uses the highest.",
        ],
        "uncertainty": {"range_factor": [RANGE_LOW, RANGE_HIGH], "note": RANGE_NOTE,
                        "evidence": ["Short text prompt energy: 0.24 Wh (Google, median Gemini), ~0.3 Wh (Epoch AI, GPT-4o), "
                                     "0.34 Wh (OpenAI), 0.42 Wh (Jegham et al., GPT-4o).",
                                     "Water per Wh: onsite 0.12–1.9 mL (provider and location), electricity-generation "
                                     "1.3–9.5 mL (US states, Li et al.), so ~1.4–11 mL comprehensive vs 4.1 used here."]},
        "limitations": [
            "Vendor figures are not peer-reviewed, describe median prompts and exclude model training.",
            "Electricity-generation water uses US grid averages; real figures depend on data-centre location and grid mix.",
            "Results are indicative estimates, not measurements.",
        ],
        "sources": SOURCES,
        "how_to_cite": (f"Lamb, N. (2026). An energy-first method for estimating the water and energy footprint of AI use "
                        f"(methodology {METHODOLOGY_VERSION}) [Preprint]. Zenodo. https://doi.org/{METHOD_NOTE_DOI}"
                        if METHOD_NOTE_DOI else
                        f"PharmaTools.AI AI Water & Energy Calculator, methodology {METHODOLOGY_VERSION}. {PAGE_URL}"),
        **_meta(),
    }


def compare_water_use(water_ml: float) -> dict:
    if not (0 < water_ml <= 1e12):
        raise InputError("water_ml must be a positive number")
    lifecycle = []
    for label, ml in LIFECYCLE_ITEMS:
        ratio = water_ml / ml
        lifecycle.append({"item": label, "item_water": fmt_water(ml),
                          "fraction_of_item": _r(ratio, 2),
                          "plain": (f"{ratio:.2g} of one {label}" if ratio < 1 else f"{ratio:.3g} x one {label}")})
    prompts = water_ml / (ENERGY_PER_QUERY_WH["simple"] * WATER_PER_WH_ML["comprehensive"])
    return {
        "water": fmt_water(water_ml),
        "everyday": water_equivalents(water_ml),
        "lifecycle_comparisons": lifecycle,
        "equivalent_text_prompts_comprehensive": round(prompts),
        "caveat": ("Lifecycle items are full 'virtual water' footprints (including rainwater for crops), a much wider "
                   "boundary than AI operational water. Use them for scale, not like-for-like. Almond irrigation and "
                   "data-centre cooling also draw on different water supplies."),
        **_meta(),
    }


def estimate_session_footprint(input_tokens: int, output_tokens: int, cached_input_tokens: int = 0,
                               model_class: str = "frontier", boundary: str = "comprehensive") -> dict:
    model_class = _check_choice(model_class, MODEL_CLASS_FACTOR, "model_class")
    boundary = _check_choice(boundary, WATER_PER_WH_ML, "boundary")
    for name, v in (("input_tokens", input_tokens), ("output_tokens", output_tokens),
                    ("cached_input_tokens", cached_input_tokens)):
        if v < 0 or v > MAX_TOKENS:
            raise InputError(f"{name} must be between 0 and {MAX_TOKENS:,}")
    if input_tokens + output_tokens + cached_input_tokens == 0:
        raise InputError("Pass at least one non-zero token count")
    eff_input = input_tokens + CACHE_TO_INPUT * cached_input_tokens + OUTPUT_TO_INPUT * output_tokens
    central_wh = eff_input * WH_PER_INPUT_TOKEN * MODEL_CLASS_FACTOR[model_class]
    w = WATER_PER_WH_ML[boundary]
    lo, hi = central_wh * RANGE_LOW, central_wh * RANGE_HIGH
    prompt_equiv = central_wh / ENERGY_PER_QUERY_WH["simple"]
    notes = [
        f"Order-of-magnitude estimate. Calibrated so ~{CALIB_INPUT:,} input + ~{CALIB_OUTPUT} output tokens on a frontier model = {ENERGY_PER_QUERY_WH['simple']} Wh (one typical chat prompt).",
        f"Assumes output tokens cost ~{OUTPUT_TO_INPUT:g}x input tokens and cache reads ~{CACHE_TO_INPUT:g}x. Real values depend on model, hardware, batching and data centre.",
        RANGE_NOTE,
        "Pass the SUM of tokens across every model call in the session – agentic loops resend the context each turn.",
    ]
    if model_class == "reasoning":
        notes.append("For reasoning models, include hidden reasoning/thinking tokens in output_tokens.")
    return {
        "inputs": {"input_tokens": input_tokens, "output_tokens": output_tokens,
                   "cached_input_tokens": cached_input_tokens, "model_class": model_class, "boundary": boundary},
        "central": {"energy_wh": _r(central_wh, 3), "water_ml": _r(central_wh * w, 3),
                    "energy": fmt_energy(central_wh), "water": fmt_water(central_wh * w)},
        "range": {"energy_wh": [_r(lo, 2), _r(hi, 2)], "water_ml": [_r(lo * w, 2), _r(hi * w, 2)],
                  "water": f"{fmt_water(lo * w)} – {fmt_water(hi * w)}"},
        "equivalent_chat_prompts": round(prompt_equiv, 1),
        "water_equivalents": water_equivalents(central_wh * w),
        "confidence": "low – indicative only",
        "assumptions": notes,
        **_meta(),
    }


def _meta() -> dict:
    meta = {"methodology_version": METHODOLOGY_VERSION, "reviewed": REVIEWED, "source": PAGE_URL}
    if METHOD_NOTE_DOI:
        meta["method_note"] = f"https://doi.org/{METHOD_NOTE_DOI}"
    return meta
