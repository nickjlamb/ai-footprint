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


def test_root_redirects_to_docs(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "https://www.pharmatools.ai/mcp#footprint"


def test_health(client):
    assert client.get("/health").json() == {"ok": True}
    assert client.head("/health").status_code == 200
