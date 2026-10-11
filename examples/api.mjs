// The JSON API from Node 18+ or a browser. No dependencies, open CORS.
//   node examples/api.mjs
const BASE = process.env.AI_FOOTPRINT_URL ?? "https://prompt-tightener-production.up.railway.app";

async function get(path, params = {}) {
  const res = await fetch(`${BASE}${path}?${new URLSearchParams(params)}`);
  if (!res.ok) throw new Error(`${res.status} ${(await res.json()).detail}`);
  return res.json();
}

const year = await get("/api/footprint", { queries_per_day: 30, days: 250, usage: "simple" });
console.log(`30 prompts a day for a working year: ${year.total.energy}, ${year.total.water}`);

const session = await get("/api/session", {
  input_tokens: 200000, output_tokens: 40000, cached_input_tokens: 3000000,
});
console.log(`One agent session: ${session.central.water} (range ${session.range.water})`);

const both = await Promise.all(["onsite", "comprehensive"].map((boundary) =>
  get("/api/footprint", { queries_per_day: 1, boundary })));
console.log(`One prompt: ${both[0].per_query.water_ml} mL onsite vs ${both[1].per_query.water_ml} mL comprehensive`);
