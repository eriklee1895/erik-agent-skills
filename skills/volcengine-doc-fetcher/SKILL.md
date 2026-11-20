---
name: volcengine-doc-fetcher
description: >
  Fetch Volcano Engine (火山引擎) official documentation pages as clean Markdown. Use this skill whenever the user provides a volcengine.com / volces.com doc URL, wants to look up a Volcano Engine API reference, needs to check API parameters, models, or product documentation from 火山引擎, or mentions 火山引擎文档/火山引擎API/火山引擎接口文档. Also use when the user says "查一下火山引擎的...", "帮我看一下豆包/方舟/Seedance 的 API 文档", or pastes an ark.volcengine.com / docs.volcengine.com / www.volcengine.com/docs URL. Prefers the platform's native no-auth Markdown endpoints (curl, no browser) and only falls back to headless Chromium / Firecrawl for pages without a Markdown endpoint. This skill should ALWAYS be used for fetching Volcano Engine doc pages rather than hand-crafting HTTP calls.
---

# Volcengine Doc Fetcher

Fetch Volcano Engine official documentation as clean Markdown. Most Volcano doc pages now expose **native Markdown endpoints**, so the common path is a plain HTTP GET with no browser, no login and no cost. Headless rendering remains only as a last-resort fallback for the shrinking set of pages without a Markdown endpoint.

## Quick Start

```bash
# Any of the three supported URL shapes — native Markdown is picked automatically
uv run scripts/fetch.py "https://ark.volcengine.com/region:cn-beijing/docs/overview"
uv run scripts/fetch.py "https://docs.volcengine.com/docs/ark/quick-start-console?lang=zh"
uv run scripts/fetch.py "https://www.volcengine.com/docs/6561/2499930"

# Multiple URLs (concurrent), save Markdown + metadata to a directory
uv run scripts/fetch.py --output-dir ./volcengine-docs/ url1 url2 url3

# Native Markdown only, fail rather than launch a browser
uv run scripts/fetch.py --method markdown "https://docs.volcengine.com/docs/zh/ark/multi-agent.md"
```

The Markdown tier only needs `curl`, so it also runs under a plain `python3 scripts/fetch.py …` without installing the PEP 723 browser dependencies. `uv run` is still the default because the rendering fallback needs them.

## Native Markdown URL rules (the important part)

A naive "append `.md` to the browser URL" does **not** work on every host. The script encodes these verified rules; understand them when constructing URLs by hand.

| Platform | Browser URL | Canonical Markdown URL |
|---|---|---|
| Ark docs | `https://ark.volcengine.com/region:cn-beijing/docs/<slug>` | same path + `.md` |
| Ark console mirror | `https://console.volcengine.com/ark/region:cn-beijing/docs/<slug>` | same path + `.md` (byte-identical to the ark host) |
| Unified doc center | `https://docs.volcengine.com/docs/<product>/<slug>?lang=zh` | **insert a language segment**: `/docs/zh/<product>/<slug>.md` |
| BytePlus (international) | `https://docs.byteplus.com/docs/<product>/<slug>` | `/docs/en/<product>/<slug>.md` |
| Legacy numeric docs | `https://www.volcengine.com/docs/<product>/<doc_id>` | 301/302 redirects to a doc-center path, which is then transformed as above |

Gotcha: on `docs.volcengine.com`, appending `.md` directly to the browser URL (without the `/zh/` segment) returns an HTML SPA page or a TOS `NoSuchKey` 404 — even though the page is a real doc. The language-segment form is the correct one.

### llms.txt index hierarchy

- Doc-center root index: `https://docs.volcengine.com/llms.txt` — every product library, with Chinese/English and the BytePlus international entry.
- Per-product library: `https://docs.volcengine.com/docs/zh/<product>/llms.txt` (e.g. `/docs/zh/ark/llms.txt`, `/docs/zh/doubao-voice/llms.txt`) — every page in that product with its exact Markdown URL and a one-line summary.
- Ark platform: `https://ark.volcengine.com/llms.txt` (index) and `llms-full.txt` (full Markdown of all public Ark docs, ~9 MB); also `sitemap.xml` and `models.json`.
- When you do not know a page's canonical Markdown URL, find it in the product `llms.txt` instead of guessing the path transform.

## Fetch strategy (three tiers, cheapest first)

`scripts/fetch.py` tries in order and stops at the first success:

1. **`markdown` (tier 1, default first choice)** — resolves the URL to its native Markdown endpoint and GETs it via `curl`. Stdlib Python + curl only; handles BOM stripping, 404/HTML-fallback detection, and legacy redirect bridging. `curl` uses the system trust store, so it works behind proxies with custom CA bundles where Python's `urllib` would fail certificate verification.
2. **`playwright` (tier 2)** — headless Chromium renders the JS SPA, extracts the doc content area (`[class*="content"][class*="doc"]`), strips chrome/noise, and converts via `markdownify`. Only reached when no Markdown endpoint exists. Heavy imports are lazy, so tier 1 never pays for them.
3. **`firecrawl` (tier 3)** — `firecrawl scrape --wait-for 5000` external fallback when local rendering fails. Requires the authenticated CLI and consumes credits.

| `--method` | Behavior |
|---|---|
| `auto` (default) | native Markdown → Playwright → Firecrawl |
| `markdown` | native Markdown endpoints only; error if the URL matches no known rule (no browser) |
| `playwright` | headless Chromium only |
| `firecrawl` | Firecrawl CLI only |

## agent-browser vs the built-in Playwright fallback

The separate `agent-browser` CLI is good at Markdown *discovery* but is not a replacement for the rendering fallback:

- `agent-browser read <url>` negotiates `Accept: text/markdown`, probes `.md`, and walks ancestor paths to the nearest `llms.txt` to find a matching link — all **without launching a browser** (`lifecycle.browserLaunched: false`, reported `source: accept-markdown`). This overlaps tier 1 and is a useful manual escape hatch when this script's host rules do not recognize a URL.
- Its one-shot `read` does **not** execute JavaScript: a pure JS SPA with no Markdown endpoint returns near-empty content. Real rendering needs the stateful `agent-browser open <url>` → `read` (active tab) → `close --all` flow, which holds a browser daemon and global active-tab state. That does not fit this script's concurrent, stateless batch model.
- Keep Playwright as the in-script JS fallback (one-shot, selector-scoped, async, no shared session). Reach for `agent-browser read` interactively when a URL is unknown to the resolver and you want its `llms.txt` walk to locate the Markdown source.

## Prerequisites

- Tier 1: `python3` 3.12+ and `curl` on PATH — nothing else.
- Tier 2: `uv` plus `playwright`/`beautifulsoup4`/`markdownify`/`lxml` (declared in the script's PEP 723 metadata) and a Chromium build: `uvx playwright install chromium`.
- Tier 3: authenticated `firecrawl` CLI.

## CLI reference

```
uv run scripts/fetch.py [OPTIONS] URL [URL...]
```

| Flag | Default | Description |
|---|---|---|
| `--method` | `auto` | `auto` / `markdown` / `playwright` / `firecrawl` |
| `--output-dir`, `-o` | — | Save each URL as `{slug}.md` + `{slug}.meta.json` instead of printing |
| `--no-cache` | — | Bypass cache and force re-fetch |
| `--cache-ttl` | `3600` | Cache TTL in seconds |
| `--concurrency`, `-c` | `3` | Max concurrent fetches |
| `--json` | — | JSON array to stdout (url, title, method, cached, markdown) |
| `--timeout` | `30` | Per-request timeout in seconds |

Slugs: legacy numeric URLs → `6561-163032`; Ark/doc-center word slugs → last two path segments joined (e.g. `ark-quick-start-console`).

## Output and caching

- stdout mode prints each Markdown body separated by `---`; `--json` wraps results with metadata; `-o` writes one `.md` + `.meta.json` pair per URL.
- Cache lives at `~/.cache/volcengine-docs/`, keyed by URL slug, shared across projects. TTL default 1 hour; `--no-cache` forces a refresh.
- Native Markdown bodies get BOM removal and blank-line normalization; Playwright bodies additionally drop zero-width spaces and inline base64 icons. A 404 JSON body or HTML content-type on a supposed Markdown URL is treated as a miss, not returned as content.

## Error handling

- A native-Markdown miss (no matching URL rule, non-200, or non-Markdown content type) falls through to Playwright in `auto` mode, or returns an error in `markdown` mode.
- Legacy redirects that do not land on a doc-center host give up the Markdown route and fall through to rendering.
- Per-URL failures are reported independently and never abort the other URLs; the process exits non-zero if any URL failed.
- Firecrawl/Playwright unavailable: the error names the missing dependency.

## When to use

- Any `volcengine.com` / `volces.com` doc URL (Ark, doc-center, or legacy numeric), Volcano Engine API parameter/model lookups, 火山引擎文档/接口/豆包/方舟/Seedance documentation requests.
- Batch-collecting official docs into a local knowledge base (pair `-o` with a product `llms.txt` URL list).

## When NOT to use

- General web search about Volcano Engine — use the `volcengine-web-search` skill.
- Non-Volcano Engine URLs — use generic web/fetch tooling.
- TTS voice generation → `volcengine-tts`; image/video generation → `seedream-image-gen` / `seedance-video-gen`.
