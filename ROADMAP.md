# Roadmap

Where AI Footprint is heading. Nothing here has a date. Priorities move as better sources appear and as people say what they need, so if something here matters to you, [open an issue](https://github.com/nickjlamb/ai-footprint/issues/new/choose) or add a 👍 to an existing one.

Two rules apply to everything below:

1. **The tools stay deterministic.** No model in any footprint tool. Same input, same answer.
2. **The calculator page and the server stay in step.** A figure changes in both or in neither.

## Next

- **Grid-aware water intensity.** The `comprehensive` boundary uses a US grid average for the water consumed generating electricity. Add an optional `region` parameter with published per-country or per-grid factors, and say in the result which factor was used.
- **Pin a methodology version.** Let callers request a specific `methodology_version`, so a figure quoted in a report can be reproduced exactly after the methodology moves on.
- **MCP resources and prompts.** Expose the methodology and sources as an MCP resource, and add prompt templates such as "explain this AI water figure" and "estimate this session".
- **OpenAPI description.** Publish a static OpenAPI document for the JSON API so it can be imported into API tools and agent frameworks.

## Later

- **Per-image and per-video tiers.** Replace the single `intensive` tier with figures per generated image and per second of video, once disclosures are good enough to support them.
- **Shared rate limiting.** Move rate limits from memory to a shared store, so the server can run on more than one instance.
- **Container image.** A published Docker image for one-command self-hosting.

## Exploring

These need more evidence or more thought before they're committed to.

- **Training amortisation.** An optional, clearly labelled share of training energy per prompt. Published training figures are sparse and the right amortisation is contested.
- **Provider-specific profiles.** Separate figures per provider, where each publishes comparable data. Today the methodology deliberately uses the most conservative published onsite figure.
- **Carbon.** Emissions alongside energy and water. This depends on the same grid data as the first item under "Next".

## Done

See the [changelog](CHANGELOG.md).
