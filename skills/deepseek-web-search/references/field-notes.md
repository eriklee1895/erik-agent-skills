# Field notes: DeepSeek Search/Fetch probe

Measured 2026-10-17 on `api.deepseek.com`, with 60+ calls (about ¥0.4). One
operator, one day, one query set — treat these as directional findings, not a
benchmark. Re-run before making pricing or routing decisions.

## Official documentation

Checked 2026-10-17. These pages define the contract; this file records where the
observed behavior differs from it. Re-check prices, limits, and error codes
before depending on them.

| Page | URL | Covers |
| --- | --- | --- |
| Guide (中文) | <https://api-docs.deepseek.com/zh-cn/guides/search> | endpoints, search syntax, per-success billing, QPS, 403/404/429/504 semantics |
| Search reference (中文) | <https://api-docs.deepseek.com/zh-cn/api/search> | request/response schema, `count` 1–50, `authority` 0–4 (`-1` unknown), `rerank_score` 0–3 |
| Fetch reference (中文) | <https://api-docs.deepseek.com/zh-cn/api/fetch> | URL constraints (≤8192 chars, http/https, no userinfo), response schema |
| Pricing (中文) | <https://api-docs.deepseek.com/zh-cn/quick_start/pricing> | ¥5/1,000 successful Search/Fetch calls; model token prices |
| Release note | <https://api-docs.deepseek.com/zh-cn/news/news261017/> | 2026-10-17 launch; harness server-tool calls free until 2026-11-01 |

English equivalents: [`/guides/search`](https://api-docs.deepseek.com/guides/search),
[`/api/search`](https://api-docs.deepseek.com/api/search),
[`/api/fetch`](https://api-docs.deepseek.com/api/fetch).

## Method

- 12 Chinese queries across policy, regulation, news, API docs, papers, hotels, company, concepts, code, health, FX, exams.
- 14 English developer/RAG/agent queries with a hand-picked canonical domain each.
- 6 operator checks (`site:`, `-site:`, `lang:`, `after:`, quoted phrase).
- Mechanics: counts 1/50, `need_content`, `ori_question`, `localization`, invalid inputs, 8-way burst.
- 30 fetch targets: official docs, GitHub, arXiv abs/HTML/PDF, Chinese gov, WeChat/Zhihu/Xiaohongshu, CSDN/Juejin, 404 and timeout cases.

## Chinese queries

| Query | Canonical rank | Observation |
| --- | --- | --- |
| 新能源汽车购置税政策 | 1 (miit.gov.cn) | Official first, but #2–3 were unrelated local-government complaint pages |
| 生成式AI管理办法全文 | 1 (gov.cn) | 10/10 gov.cn, best case |
| DeepSeek 1017 发布 | 1 (api-docs) | Official 1–2, then media |
| DeepSeek API 上下文长度 | 1 (api-docs) | Official first; vendor mirrors and a GitHub copy follow |
| MoE 路由论文 | 7 (ar5iv mirror) | ACM/AAAI/ACL good; `arxiv.org` itself absent |
| 杭州西湖酒店 | 1 (ctrip) | Only 4 unique domains; affiliate duplicates |
| 字节跳动营收 | none | Sohu reposts 3/10; no official or primary filing |
| RAG vs 长上下文 | none | Tencent/Aliyun developer articles dominate; no paper |
| Python asyncio TaskGroup | none | No `docs.python.org` in top 10; raw GitHub notes and Google source mirrors |
| 高血压用药指南 | none | UpToDate/PubMed/ACC strong; Chinese guideline site absent |
| 人民币汇率 | 6 (chinamoney) | Wise ranks 1–2 above the official CFETS/PBoC pages |
| 考研报名时间 | 1 (neea) | Official first, then training-school content |

Takeaway: strong for policy, regulation, and official announcements; weak for
English-centric technical topics and for primary sources on company/finance
questions. Portal duplicates are common.

## English developer queries

| Query | Official domain in top 10 | Canonical English page rank | What crowded it out |
| --- | --- | --- | --- |
| Python 3.14 what's new | yes | 1 (but `/zh-cn/`, `/zh-tw/`, `/pl/3.15`) | localized editions, Persian mirror |
| OpenAI Responses web search pricing | **no** | — | Simon Willison posts, GitHub PRs, raw skill files, Russian news |
| Claude Agent SDK | yes | 1 (`code.claude.com`) | `mintlify.wiki` clones, GitHub copies |
| LangGraph HITL | yes | 1 (`docs.langchain.com`) | pypi packages, `mintlify.wiki` |
| RAG chunking benchmark | no (`arxiv.org`) | — | IEEE/ACM/ACL papers, `ezproxy` mirror |
| vLLM prefix caching | yes | 1 (`docs.vllm.ai`) | `.com.cn` mirror, `mintlify.wiki` |
| MCP specification | yes | 1 (`modelcontextprotocol.io`) | `.info` / `.com.cn` lookalikes |
| Qwen3 quantization | **no** (`huggingface.co`) | — | pypi `llmcompressor`, GitHub forks, CSDN |
| pgvector HNSW | yes (`github.com`, wrong repos) | 3 | Alibaba Cloud zh page, random GitHub files, Supabase |
| Agent memory survey | no (`arxiv.org`) | — | Semantic Scholar, GitHub notes, `ezproxy` mirrors |
| Next.js 16 migration | yes (`nextjs.org`) | 6 | agency blogs, random GitHub repos, npm packages |
| Kubernetes 1.34 notes | yes | 1 (ja/ko editions) | localized editions, Huawei/AWS docs |
| DeepSeek V4.1 benchmark | yes | 1 (`api-docs`) | Sohu/ media |
| OpenTelemetry GenAI conventions | yes (`opentelemetry.io`) | 6 | pypi/go packages, a `bayern` mirror, vendor blogs |

Summary: official domain present 9/14; canonical English page at rank 1 only
4/14. Localization and mirrors are systematic, not occasional.

### Operator fixes

Adding `lang:en` or `site:` moved the official domain to rank 1 in **6/6**
retest queries (`docs.python.org`, `openai.com`, `github.com`,
`huggingface.co`, `arxiv.org`). `site:` is reliable; `lang:en` is a soft hint —
the Python retest still returned a Polish page at rank 1.

`site:` also admits locale-tagged mirrors (`python-docs-zh-tw`) and lookalike
domains (`modelcontextprotocol.info`), so combine it with `--drop-localized`
and a domain check.

## Navigational ranking: official sources missing

A second 22-query probe on 2026-10-17 (same day, `count=10`) measured whether the
expected official domain appeared anywhere in the top 10:

| Set | Official domain in top 10 | MRR |
| --- | ---: | ---: |
| English `site:` probes (5) | 5/5 | 1.000 |
| English navigational (10) | 7/10 | 0.575 |
| Chinese (5) | 4/5 | 0.650 |
| Chinese `site:` (2) | 2/2 | 1.000 |
| **Total** | **18/22** | **0.727** |

The four misses: OpenAI GPT-6 release notes (`tech.yahoo.com` first, `openai.com`
absent), SEC EDGAR Apple 10-K (`origin.rootz.global` first, `sec.gov` absent),
EU AI Act timeline (`bsigroup.com` first, `europa.eu` absent), and 中央气象台
台风路径 (`news.qq.com` first, `nmc.cn` absent). 北京公积金 put a raw IP
(`219.237.218.35`) at rank 1.

`authority` does not separate these: the portals scored 3–4 and the raw IP
scored 4, while the official pages were missing. Sorting by authority is a
no-op; `site:` is the only reliable lever (5/5 rank 1 above).

Ordering is not stable between identical runs: a later rerun of the SEC query
returned `sec.gov` at rank 5. Read the table as failure modes, not fixed ranks.

## Mechanics

| Check | Result |
| --- | --- |
| `count=1` / `count=50` | 1 / 50 results; 50 is mostly pypi, npm, socket.dev, and duplicate framework docs |
| `need_content` | Works; content is **unescaped** Markdown with `¶` anchors |
| `fetch` content | **Fully escaped** Markdown (`\#`, `\-`, `\.`); headings recover after unescaping |
| Empty query | 400, `'query' must not be empty` |
| `count=51` | 400, `'count' must be between 1 and 50` |
| Bad key | 401, masked key in message |
| 8 parallel calls | 200×5, 429×3; body reports `Your current QPS: 5` |
| Search latency | 236–826ms, p50 ≈ 430ms |
| Fetch latency | 0.1–17s for successes; 30s timeouts for `python.org` and CSDN |
| `ori_question` | No visible change in a single test |
| `localization` | Returned mixed Taiwan/360-map results for a cityless query; not a geocoder |

## Fetch coverage

| Target | Status | Chars | Note |
| --- | --- | --- | --- |
| docs.python.org/3/whatsnew/3.14 | 200 | 130,748 | 8s; escaped; no fences/tables |
| docs.python.org (home) | 504 | 0 | 30s timeout |
| kubernetes.io/docs/concepts | 200 | 9,971 | escaped; 6 headings after cleanup |
| react.dev/learn | 200 | 13,026 | 3.7s |
| postgresql.org/docs/current/sql-select | 200 | 64,993 | 10.7s; code flattened to text |
| docs.aws.amazon.com S3 guide | 200 | 38,747 | 16.9s; cookie banner included |
| arxiv.org/abs/1706.03762 | 200 | 3,297 | abstract page |
| arxiv.org/html/1706.03762v7 | 200 | 41,847 | HTML edition works |
| arxiv.org/pdf/1706.03762 | **404** | 0 | PDF unsupported |
| platform.openai.com/docs | **404** | 0 | |
| docs.anthropic.com | **404** | 0 | |
| huggingface.co model/blog | **404** | 0 | two URLs |
| docs.docker.com/engine/install | **404** | 0 | |
| raw.githubusercontent.com README | **404** | 0 | text/plain rejected |
| openai.com/index, anthropic.com/news | **404** | 0 | |
| zhihu.com, x.com, xiaohongshu.com | **404** | 0 | anti-bot |
| blog.csdn.net article | 504 | 0 | 30s timeout |
| juejin.cn post | 200 | 45,315 | only when URL came from search |
| gov.cn policy page | 200 | 833 | correct metadata, thin body |

After unescaping, headings and lists recover, but **code fences, table pipes, and
link targets do not** — the extractor flattens them. For code-heavy API docs,
prefer `search --content` or a dedicated scraper.

## Implications encoded in the skill

1. Unescape fetch output, strip `¶` and boilerplate; expose `--raw` for debugging.
2. Prefer `search --content` over `fetch` when the URL came from search.
3. Default `count=10`; warn that 50 is noisy.
4. Offer `--lang`, `--drop-localized`, `--site`, `--dedupe-domain`, `--exclude-domains`.
5. Document fetch's 404/timeout matrix and the code/table/link loss.
6. Retry 429/5xx with backoff; fail fast on 400/401/402/403/404.
7. Report `authority` as a weak signal, not a filter.
8. Classify official/primary hosts locally; warn when the top 3 has none, and
   offer `--sort official` / `--official-only` without silently dropping rows.
9. Treat raw IP hosts as a low-trust marker in output and `quality.ip_hosts`.
