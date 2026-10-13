# Security policy

## Supported versions

The hosted endpoint always runs the latest release. For self-hosted deployments, security fixes go into the latest release only.

| Version | Supported |
|---|---|
| 1.x | ✅ |

## Reporting a vulnerability

Please **don't open a public issue**. Report it privately through [GitHub's private vulnerability reporting](https://github.com/nickjlamb/ai-footprint/security/advisories/new).

Include what you found, how to reproduce it, and what an attacker could do with it. You'll get an acknowledgement within 3 working days and an assessment within 10. Once a fix is released, you'll be credited in the advisory unless you'd rather not be.

## Scope

In scope:

- The server code in this repository.
- The hosted endpoint at `footprint.pharmatools.ai`: ways to bypass the CORS or rate-limit controls, reach `/tighten` from another origin, make the server log or return data it shouldn't, or exhaust its resources with small requests.
- Prompt injection through `/tighten` that gets the model to do anything other than rewrite the prompt.

Out of scope:

- Disagreement with a figure or source. That's a [methodology issue](https://github.com/nickjlamb/ai-footprint/issues/new?template=methodology.yml), and welcome.
- High-volume denial-of-service testing against the hosted endpoint. Please test rate limits against a local instance.

## What the server stores

Nothing. There's no database. Logs record which tool or endpoint was called. Tool inputs, prompts and IP addresses are not logged. Rate-limit counters are held in memory and reset when the server restarts.
