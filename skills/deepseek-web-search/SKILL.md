---
name: deepseek-web-search
description: >
  Search the web or fetch a known URL as Markdown through DeepSeek's Search and
  Fetch APIs. Use for current information, source discovery, and URL-to-Markdown
  extraction; best for Chinese policy, news, and company research, and for
  English developer, RAG, and agent docs that need official sources. Triggers:
  联网搜索, 网页搜索, 抓取网页, 读取链接, DeepSeek 搜索. Does not cover image
  search, vertical/authority filters, or site-wide crawling, and is not for
  questions answerable from general knowledge.
metadata:
  requires:
    bins: ["uv", "python3"]
---

# DeepSeek Web Search

Two public endpoints, one CLI:

- `POST /v1/tools/search` — ranked results with title, URL, snippet, summary, optional full text.
- `POST /v1/tools/fetch` — one URL to title + Markdown.

Both cost **¥5 per 1,000 successful calls**; failures and empty result sets are not billed. QPS is **5 per account**.

## Prerequisites

- `uv` on PATH.
- `DEEPSEEK_API_KEY` from <https://platform.deepseek.com/api_keys>. Resolution: `--api-key` → environment → skill `.env` → current-directory `.env`.
- Optional `DEEPSEEK_BASE_URL` for a gateway.

## Quick start

```bash
# Chinese research
uv run scripts/deepseek_search.py search "2026 新能源汽车 购置税 政策" -c 10

# English developer docs: constrain the locale and the domain
uv run scripts/deepseek_search.py search "pgvector HNSW parameters" --lang en --drop-localized --site github.com

# Full text from a known result (cleaner than fetch)
uv run scripts/deepseek_search.py search "vLLM prefix caching" --content -c 1 --json

# Authoritative only: keep official/primary domains, drop portals and raw IPs
uv run scripts/deepseek_search.py search "北京公积金贷款额度 2026" --official-only

# Unsure of the official domain? Lift official hosts instead of filtering
uv run scripts/deepseek_search.py search "WHO air quality guidelines PM2.5" --sort official

# One URL to Markdown
uv run scripts/deepseek_search.py fetch "https://arxiv.org/abs/1706.03762"
```

Use `--json` for anything downstream; human output is for reading only.

## Choose the right call

| Need | Use |
| --- | --- |
| Discover sources for a question | `search` |
| Read a known page's text | `search --content` when the page came from search; `fetch` when you only have the URL |
| Machine-readable pipeline | `search --json` / `fetch --json` |
| Authoritative sources only | `--official-only` to filter; `--sort official` to lift without dropping; `--site` when the domain is known |
| Image search, time/authority/industry filters, weather/stock cards | Out of scope: this API exposes only query, count, content, and locale filters |
| Site-wide crawl, PDF, JS-heavy page, structured extraction | Out of scope: use a browser-based scraper |

`search --content` and `fetch` use different extractors. Search content is
readable Markdown; fetch content arrives fully escaped (`\#`, `\-`, `\.`) and the
CLI unescapes it. Both flatten code fences and link targets, and table recovery
is inconsistent — do not quote code from either as if it were the page's block.

## Output

Default output is for reading: ranked results with title, URL, date, authority,
relevance, and a summary preview. Treat it as unstable presentation, not an API.

Use `--json` for pipelines:

- `search` → `{endpoint, query, elapsed_ms, attempts, quality, api_response: {results: [...]}}`
- `fetch` → `{endpoint, url, title, content, chars, truncated, unescaped, elapsed_ms, attempts, notes}`

`quality` reports `official_count`, `official_first_rank`, `official_top3`,
`ip_hosts`, `top3_hosts`, and a `warning` string. `api_response.results` already
reflects every local filter and sort, including `--official-only` and
`--sort official`. Parse that array; do not parse the human output.

## Reading results

- `authority` is **domain-level and weakly discriminative**: Yahoo scored 3, `rsi.co.id` scored 4, and a bare IP (`219.237.218.35`) scored 4 while `openai.com` was absent from the same result set. Treat it as a tiebreaker, not a filter.
- `rerank_score` clusters in 1.3–2.9; the documented `≥1.5 = 优质` threshold passes almost everything. Rank order is more informative than the absolute score.
- `date` is often missing or stale; `site_name`, `url`, and the actual summary text are the reliable signals.
- Duplicate reposts are common on Chinese portals. Use `--dedupe-domain` and `--exclude-domains sohu.com,163.com`.
- Human output tags `official` and `raw-ip` hosts; `--json` exposes the same signals under `quality`.

## Default ranking is not authoritative (22-query probe)

Measured 2026-10-17, 22 Chinese/English queries at `count=10`: an official or
primary domain reached the top 10 in 18, but four navigational queries missed it
entirely.

| Query | Top 1 | Official domain |
| --- | --- | --- |
| OpenAI GPT-6 release notes | `tech.yahoo.com` | `openai.com` absent |
| SEC EDGAR Apple 10-K 2025 | `origin.rootz.global` | `sec.gov` absent |
| EU AI Act implementation timeline | `bsigroup.com` | `europa.eu` absent |
| 中央气象台 台风路径 | `news.qq.com` | `nmc.cn` absent |

`authority` cannot repair this: the portals scored 3–4 and the raw IP scored 4,
while the official pages were missing or buried. Ordering varies between
identical runs — a later SEC rerun put `sec.gov` at rank 5 — so read the table
as failure modes, not fixed ranks. Use these levers, cheapest first:

1. `--site <official-domain>` — the only reliable fix: all 5 `site:` probes in this set landed rank 1, and 6/6 earlier retests moved the official domain to rank 1. For navigational queries (brand + docs/release/pricing/spec), add it up front.
2. `--sort official` — lifts official/primary hosts while keeping the original order inside each group. Use when the domain is unknown; still read titles, because an official page can be irrelevant.
3. `--official-only` — hard filter for government, education, IGO, arXiv/GitHub, and curated vendor docs. On `北京公积金贷款额度 2026` it cut 10 portal rows to 3 government originals; when the filter empties the set, the CLI tells you to retry with `--site`.
4. The CLI warns on stderr when the top 3 contain no official host, and records the same warning in `quality.warning`.

## English developer queries: expect localization and mirrors

Measured on 14 English dev/RAG/agent queries (2026-10-17): the official domain
appeared in 9/14 top-10 lists, but the **canonical English page at rank 1 only
4/14**. The rest were localized editions (`docs.python.org/pl`, `/ja`, `/zh-tw`)
or mirrors (`mintlify.wiki`, `ar5iv.labs.arxiv.org`, `*.ezproxy.*`,
`raw.githubusercontent.com`).

Use these in order:

1. `--lang en` — a hint, not a filter. It still returned `/pl/` and `/zh-tw/` pages.
2. `--drop-localized` — drops `/ja/`, `/zh-cn/`, `/pl/` paths and locale-tagged mirrors.
3. `--site <domain>` — the strongest lever. In 6/6 probe queries the official domain moved to rank 1. It still admits localized editions: `site:docs.python.org` returned a `/ja/` page in a later run, so pair it with `--drop-localized`.
4. For critical APIs, fetch the page from the official URL you already know. Search ordering varies between identical runs; pin the domain and verify the path.

Canonical domains worth pinning with `--site`:

| Topic | Domain |
| --- | --- |
| Python | `docs.python.org` |
| OpenAI API | `platform.openai.com`, `openai.com` |
| Anthropic / Claude | `platform.claude.com`, `code.claude.com`, `anthropic.com` |
| LangChain / LangGraph | `docs.langchain.com`, `langchain-ai.github.io` |
| MCP | `modelcontextprotocol.io` |
| vLLM | `docs.vllm.ai` |
| Hugging Face | `huggingface.co` |
| Postgres / pgvector | `postgresql.org`, `github.com` |
| Papers | `arxiv.org` |
| Next.js | `nextjs.org` |
| Kubernetes | `kubernetes.io` |

## Fetch limits (measured)

| Works | Fails with 404 | Times out |
| --- | --- | --- |
| `docs.python.org`, `kubernetes.io`, `react.dev`, `postgresql.org`, `docs.aws.amazon.com`, `arxiv.org/abs`, `arxiv.org/html`, `modelcontextprotocol.io`, Juejin (URL from search) | `platform.openai.com`, `docs.anthropic.com`, `huggingface.co` (model/blog), `openai.com/index`, `anthropic.com/news`, `docs.docker.com`, `raw.githubusercontent.com`, arXiv PDF, Zhihu, X, Xiaohongshu | `python.org` home, CSDN (both 30s) |

- Successful fetches took 0.1–17s; PDF and plain-text URLs are rejected (`404`).
- `404` means "no extractable content", not necessarily a dead link. Fall back to `search --content` on the same source, then a browser-based scraper.
- `504` is an upstream timeout; retrying the same slow site rarely helps. Raise `--timeout` once, then switch tools.

## Errors and retries

| Status | Meaning | Action |
| --- | --- | --- |
| 400 | Invalid query/count/URL | Fix input; the message names the field |
| 401 | Bad key | Recheck `DEEPSEEK_API_KEY` |
| 402 | No balance | Top up |
| 403 | Fetch blocked by policy | Try the official mirror or another extractor |
| 404 | No extractable content | `search --content`, then a browser-based scraper |
| 429 | QPS exceeded | Wait 1–2s; the message reports `current QPS: 5` |
| 5xx | Server/upstream failure | Retry with backoff |

The CLI retries 408/429/5xx with exponential backoff (2 attempts for search,
1 for fetch); all other statuses fail fast with a hint.

## Cost control

- `count` does not change price, but `count=50` is mostly pypi/npm/socket noise. Use 10, and at most 20 when filtering.
- A search + fetch pair costs ¥0.01. The probe suite behind this skill (60+ calls) cost about ¥0.4.
- QPS 5 is per account: 8 parallel calls produced 3×429. Serialize batch work or add a small delay.

## Workflow

1. `search` with 10 results; add `--lang en --drop-localized --site` for English dev topics.
2. Check `quality.warning`. No official host → retry with `--site` (or `--official-only` when the user asked for authoritative sources); official host buried below rank 3 → `--sort official`.
3. Prefer official/primary sources; ignore content farms and mirrors; check the date.
4. If summaries are insufficient, take the URL and run `search --content` (clean) before `fetch`.
5. Cite `title`, `url`, and `date`. Never present flattened code as if it were the page's code block.
6. If fetch returns 404, switch to `search --content` or a browser-based scraper.

See `references/field-notes.md` for the official documentation links and the measured probe data behind these rules.
