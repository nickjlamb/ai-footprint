"""Run with: MOCK=1 pytest -q   (MOCK avoids needing an Anthropic key)"""
import os

os.environ.setdefault("MOCK", "1")

import pytest
from fastapi.testclient import TestClient

import footprint as fp
from main import app


# --- parity with the live calculator page -------------------------------------
def test_matches_page_default_view():
    # Page default: 25 queries/day, simple text, comprehensive -> 8.5 Wh, 34.8 mL per day
    r = fp.estimate_ai_footprint(25, "simple", "comprehensive", 1)
    assert r["per_day"]["energy"] == "8.5 Wh"
    assert r["per_day"]["water"] == "34.8 mL"


def test_matches_page_annual_view():
    # Page annual (250 workdays): 2.1 kWh, 8.7 L
    r = fp.estimate_ai_footprint(25, "simple", "comprehensive", 250)
    assert r["total"]["energy"] == "2.1 kWh"
    assert r["total"]["water"] == "8.7 L"


def test_onsite_boundary_and_aliases():
    r = fp.estimate_ai_footprint(10, "text", "reported")
    assert r["inputs"]["usage"] == "simple" and r["inputs"]["boundary"] == "onsite"
    assert r["per_query"]["water_ml"] == 0.34


def test_session_calibration_anchor():
    r = fp.estimate_session_footprint(1000, 400)
    assert abs(r["central"]["energy_wh"] - 0.34) < 1e-6
    assert r["equivalent_chat_prompts"] == 1.0
    lo, hi = r["range"]["energy_wh"]
    assert lo < 0.34 < hi


def test_cached_tokens_are_cheaper():
    a = fp.estimate_session_footprint(100_000, 0)["central"]["energy_wh"]
    b = fp.estimate_session_footprint(0, 0, cached_input_tokens=100_000)["central"]["energy_wh"]
    assert b == pytest.approx(a * 0.1, rel=1e-2)


@pytest.mark.parametrize("kwargs", [
    dict(queries_per_day=0), dict(queries_per_day=5, usage="huge"),
    dict(queries_per_day=5, days=0), dict(queries_per_day=5, boundary="global"),
])
def test_bad_inputs(kwargs):
    with pytest.raises(fp.InputError):
        fp.estimate_ai_footprint(**kwargs)


def test_compare():
    r = fp.compare_water_use(12_000)
    almond = [x for x in r["lifecycle_comparisons"] if "almond" in x["item"]][0]
    assert almond["fraction_of_item"] == 1.0
    assert "caveat" in r


# --- HTTP layer -------------------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_api_footprint_open_cors(client):
    r = client.get("/api/footprint?queries_per_day=25", headers={"Origin": "https://example.com"})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "*"
    assert r.json()["per_day"]["water"] == "34.8 mL"


def test_api_bad_input_is_400(client):
    assert client.get("/api/footprint?queries_per_day=5&usage=huge").status_code == 400


def test_tighten_cors_still_strict(client):
    r = client.options("/tighten", headers={"Origin": "https://evil.example",
                                            "Access-Control-Request-Method": "POST"})
    assert r.status_code == 400
    r = client.options("/tighten", headers={"Origin": "https://www.pharmatools.ai",
                                            "Access-Control-Request-Method": "POST"})
    assert r.headers["access-control-allow-origin"] == "https://www.pharmatools.ai"


def test_every_tool_has_title_and_read_only_annotations():
    import asyncio

    from mcp_tools import mcp

    tools = asyncio.run(mcp.list_tools())
    assert len(tools) == 4
    for t in tools:
        assert t.title and t.annotations.title == t.title
        assert t.annotations.readOnlyHint is True and t.annotations.destructiveHint is False


def test_root_redirects_to_docs(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "https://www.pharmatools.ai/mcp#footprint"


def test_health(client):
    assert client.get("/health").json() == {"ok": True}
    assert client.head("/health").status_code == 200


def test_client_ip_ignores_spoofed_forwarded_for():
    from main import _ip_from
    # Railway sends [client, edge]; anything further left was supplied by the caller
    assert _ip_from("203.0.113.9, 100.64.0.2", "100.64.0.3") == "203.0.113.9"
    assert _ip_from("6.6.6.6, 203.0.113.9, 100.64.0.2", "100.64.0.3") == "203.0.113.9"
    assert _ip_from("203.0.113.9", "100.64.0.3") == "203.0.113.9"
    assert _ip_from("", "100.64.0.3") == "100.64.0.3"
    assert _ip_from(" , ", "") == "?"


def test_public_rate_limit_cannot_be_dodged_by_rotating_forwarded_for(client):
    import main
    main._public.clear()
    hit = [client.get("/api/methodology", headers={"X-Forwarded-For": f"10.9.{i}.1, 198.51.100.7, 100.64.0.2"}).status_code
           for i in range(main.PUBLIC_PER_IP_PER_MIN + 1)]
    main._public.clear()
    assert hit[-1] == 429 and set(hit[:-1]) == {200}


# --- headline checker: claim reader --------------------------------------------
def test_read_claim_cors_strict(client):
    r = client.options("/read-claim", headers={"Origin": "https://evil.example",
                                               "Access-Control-Request-Method": "POST"})
    assert r.status_code == 400
    r = client.options("/read-claim", headers={"Origin": "https://pharmatools.ai",
                                               "Access-Control-Request-Method": "POST"})
    assert r.headers["access-control-allow-origin"] == "https://pharmatools.ai"


def test_read_claim_mock_and_input_caps(client):
    r = client.post("/read-claim", json={"claim": "Each AI prompt uses 2 litres of water"})
    assert r.status_code == 200 and r.json()["found"] is True and r.json()["unit"] == "L"
    assert client.post("/read-claim", json={"claim": "hi"}).status_code == 400
    assert client.post("/read-claim", json={"claim": "x" * 401}).status_code == 400


@pytest.mark.parametrize("out", [
    {}, {"found": False}, {"found": True, "low": 5},                      # missing unit
    {"found": True, "low": -1, "unit": "mL"},                             # negative
    {"found": True, "low": 5, "high": 2, "unit": "mL"},                   # inverted range
    {"found": True, "low": 5, "unit": "pints"},                           # unknown unit
    {"found": True, "low": "lots", "unit": "mL"},                         # not a number
])
def test_clean_figure_rejects_malformed(out):
    from main import _clean_figure
    assert _clean_figure(out) == {"found": False}


def test_clean_figure_fills_defaults():
    from main import _clean_figure
    r = _clean_figure({"found": True, "low": 500, "unit": "mL", "per_low": 10, "per_high": 50,
                       "year": 2023, "boundary": "bogus"})
    assert r == {"found": True, "low": 500.0, "high": 500.0, "unit": "mL", "per_low": 10.0,
                 "per_high": 50.0, "per": "prompt", "year": 2023, "boundary": "unstated"}


def test_every_estimate_carries_the_likely_range():
    r = fp.estimate_ai_footprint(25, "simple", "comprehensive", 1)
    lo, hi = r["range"]["water_ml"]
    assert abs(lo - 34.85 * 0.3) < 0.1 and abs(hi - 34.85 * 3) < 0.5
    s = fp.estimate_session_footprint(1000, 400)
    assert s["range"]["energy_wh"] == [0.1, 1.02]
    m = fp.get_methodology()
    assert m["uncertainty"]["range_factor"] == [0.3, 3.0]
    assert m["methodology_version"] == "2026-10"


def test_widget_is_embeddable_and_uses_the_server_figures(client):
    r = client.get("/widget")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    assert "frame-ancestors *" in r.headers["content-security-policy"]
    assert "x-frame-options" not in r.headers
    assert "{{" not in r.text
    assert '"simple": 0.34' in r.text and '"comprehensive": 4.1' in r.text
    assert fp.METHODOLOGY_VERSION in r.text
    js = client.get("/widget.js")
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]
    assert "{{" not in js.text and "/widget?" in js.text


def test_glama_claim_file_is_public_json(client):
    r = client.get("/.well-known/glama.json")
    assert r.status_code == 200
    body = r.json()
    assert body["$schema"] == "https://glama.ai/mcp/schemas/connector.json"
    assert body["claim"].startswith("glama_claim_")
