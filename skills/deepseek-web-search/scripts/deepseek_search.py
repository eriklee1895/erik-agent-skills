#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests>=2.32",
# ]
# ///
"""
deepseek-web-search — DeepSeek Search / Fetch CLI.

Two subcommands mirror the two public endpoints:

- search: POST https://api.deepseek.com/v1/tools/search
- fetch:  POST https://api.deepseek.com/v1/tools/fetch

The Fetch endpoint returns escaped Markdown (`\\#`, `\\-`, `\\.`) and flattens
code blocks, tables, and link targets into plain text. This CLI unescapes the
payload by default and reports the remaining fidelity loss; pass --raw to keep
the payload untouched.

Examples:
    uv run deepseek_search.py search "2026 新能源汽车 购置税 政策"
    uv run deepseek_search.py search "Python 3.14 what's new" --lang en
    uv run deepseek_search.py search "pgvector HNSW" --site github.com --json
    uv run deepseek_search.py search "vLLM prefix caching" --content --count 3
    uv run deepseek_search.py fetch "https://docs.python.org/3/whatsnew/3.14.html"
    uv run deepseek_search.py fetch "https://arxiv.org/abs/1706.03762" --json
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests

DEFAULT_BASE_URL = "https://api.deepseek.com"
ENDPOINTS = {
    "search": "/v1/tools/search",
    "fetch": "/v1/tools/fetch",
}

MAX_QUERY_CHARS = 128
MAX_URL_CHARS = 8192
MAX_COUNT = 50
DEFAULT_COUNT = 10
DEFAULT_TIMEOUT = 45
DEFAULT_MAX_CHARS = 20000
DEFAULT_CONTENT_PREVIEW = 500
RETRY_STATUS = {408, 429, 500, 502, 503, 504}

API_KEY_ENV_NAMES = ["DEEPSEEK_API_KEY"]
BASE_URL_ENV_NAMES = ["DEEPSEEK_BASE_URL"]

ERROR_HINTS = {
    400: "请求参数不合法。检查 query 长度（≤128）、count 范围（1~50）、URL 是否为 http/https。",
    401: "API Key 无效或已撤销。到 https://platform.deepseek.com/api_keys 重新生成，并确认没有多余空格。",
    402: "账户余额不足。到 https://platform.deepseek.com/top_up 充值后重试。",
    403: "Fetch 请求被安全策略拒绝（目标站点或内容类型不允许）。换用官方镜像，或改用浏览器渲染的抓取工具。",
    404: "未能获取可提取的正文。常见原因：页面是重 JS 渲染、登录墙、PDF/非 HTML、反爬站点。"
         "可改用 search --content 取同一来源的正文，或改用浏览器渲染的抓取工具。",
    408: "读取请求体超时。稍后重试。",
    413: "请求体超过大小限制。缩短 URL 或改用其他抓取方式。",
    429: "触发 QPS 限流（默认 5 QPS，账号级）。降低并发或等待 1~2 秒后重试。",
    500: "服务端内部错误。稍后重试；持续失败请携带 request_id 联系支持。",
    502: "网关错误。稍后重试。",
    503: "服务暂不可用。稍后重试。",
    504: "上游抓取或搜索超时。重试或换用其他来源；Fetch 对慢站点可能连续超时。",
}

FETCH_NOTES = [
    "DeepSeek Fetch returns escaped Markdown and flattens code blocks, tables, and link targets into plain text.",
    "Set --raw to inspect the payload before cleanup.",
]

# First path segments that mark a localized edition of a documentation site.
# English is deliberately absent: /en/ is a canonical edition, not a locale to drop.
LOCALE_SEGMENTS = {
    "ar", "bn", "cs", "da", "de", "el", "es", "fa", "fi", "fr", "he", "hi",
    "hu", "id", "it", "ja", "ko", "ms", "nl", "no", "pl", "pt", "pt-br",
    "ro", "ru", "sk", "sv", "th", "tr", "uk", "vi", "zh", "zh-cn", "zh-tw",
}

# Hosts treated as official/primary for ranking and filtering. The list is
# deliberately small: suffixes cover government, education, and intergovernmental
# domains; the named hosts cover the canonical developer docs that Chinese
# portals and mirrors otherwise outrank. It is a relevance heuristic, not a
# truth guarantee.
OFFICIAL_HOST_SUFFIXES = (
    ".gov.cn", ".gov", ".edu.cn", ".edu", ".ac.cn", ".ac.uk", ".mil", ".int", ".europa.eu",
)
OFFICIAL_HOSTS = {
    "openai.com", "anthropic.com", "deepseek.com", "python.org", "postgresql.org",
    "kubernetes.io", "rust-lang.org", "nextjs.org", "vllm.ai", "huggingface.co",
    "modelcontextprotocol.io", "langchain.com", "arxiv.org", "github.com",
    "who.int", "imf.org", "europa.eu", "un.org", "worldbank.org",
}


# ── Configuration ─────────────────────────────────────────────────────


def load_env_file(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict, ignoring comments and blank lines."""
    env: dict[str, str] = {}
    if not path.is_file():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        env[name.strip()] = value.strip().strip("\"'")
    return env


def resolve_setting(cli_value: Optional[str], env_names: list[str]) -> Optional[str]:
    """Resolve a setting from CLI, environment, skill .env, then cwd .env."""
    if cli_value:
        return cli_value.strip()
    for name in env_names:
        value = os.environ.get(name)
        if value:
            return value.strip()
    for env_path in (Path(__file__).resolve().parent.parent / ".env", Path.cwd() / ".env"):
        file_env = load_env_file(env_path)
        for name in env_names:
            if file_env.get(name):
                return file_env[name].strip()
    return None


# ── Query construction ────────────────────────────────────────────────


def normalize_site(value: str) -> str:
    """Accept a host or URL and return a bare host."""
    host = value.strip()
    host = re.sub(r"^https?://", "", host, flags=re.I)
    host = host.split("/", 1)[0].strip().rstrip(".").lower()
    if not host or " " in host:
        sys.exit(f"Error: --site 需要域名（如 github.com），收到 {value!r}。")
    return host


def build_query(args: argparse.Namespace) -> str:
    """Append CLI filters to the query using the API's search operators."""
    parts = [args.query.strip()]
    if args.site:
        sites = [normalize_site(s) for s in args.site]
        parts.append(" OR ".join(f"site:{s}" for s in sites))
    if args.lang:
        parts.append(f"lang:{args.lang}")
    if args.after:
        parts.append(f"after:{args.after}")
    if args.before:
        parts.append(f"before:{args.before}")
    return " ".join(part for part in parts if part)


def url_host(url: str) -> str:
    """Return a lowercase host with common mobile/www prefixes removed."""
    match = re.match(r"https?://([^/?#]+)", url or "", flags=re.I)
    host = (match.group(1) if match else "").lower()
    for prefix in ("www.", "m."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    return host


def is_official_host(host: str) -> bool:
    """True for government, education, IGO, and curated official documentation hosts."""
    host = (host or "").lower().removeprefix("www.")
    if not host:
        return False
    if any(host == official or host.endswith("." + official) for official in OFFICIAL_HOSTS):
        return True
    return any(host == suffix[1:] or host.endswith(suffix) for suffix in OFFICIAL_HOST_SUFFIXES)


def is_ip_host(host: str) -> bool:
    """True when the URL host is a bare IP address rather than a domain."""
    try:
        ipaddress.ip_address((host or "").strip("[]"))
    except ValueError:
        return False
    return True


def sort_rows(rows: list[dict], mode: str) -> list[dict]:
    """Stable-partition rows so official hosts come first when mode is 'official'."""
    if mode != "official":
        return rows
    return sorted(rows, key=lambda row: 0 if is_official_host(url_host(row.get("url") or "")) else 1)


def quality_summary(rows: list[dict], *, official_only: bool = False) -> dict:
    """Report whether the result set contains a usable official/primary source."""
    hosts = [url_host(row.get("url") or "") for row in rows]
    official_ranks = [index for index, host in enumerate(hosts, 1) if is_official_host(host)]
    ip_hosts = sorted({host for host in hosts if is_ip_host(host)})
    warning: Optional[str] = None
    if not rows and official_only:
        warning = "No official/primary results after --official-only. Retry without it, or pin the domain with --site."
    elif rows and not official_ranks:
        warning = (
            "Top results have no official/primary domain. For navigational queries "
            "(brand + docs/release/pricing/spec), retry with --site <official-domain>. "
            "News/lifestyle queries can ignore this."
        )
    elif official_ranks and official_ranks[0] > 3:
        warning = (
            f"Official source present but first at rank {official_ranks[0]}; "
            "use --sort official or --site to lift it."
        )
    if ip_hosts:
        note = f"Raw IP host(s) in results: {', '.join(ip_hosts)}; low trust."
        warning = f"{warning} {note}" if warning else note
    return {
        "official_count": len(official_ranks),
        "official_first_rank": official_ranks[0] if official_ranks else None,
        "official_top3": bool(official_ranks and official_ranks[0] <= 3),
        "ip_hosts": ip_hosts,
        "top3_hosts": [host for host in hosts[:3] if host],
        "warning": warning,
    }


def is_localized(url: str) -> bool:
    """True when the URL points at a localized edition.

    Catches both path locales (/ja/, /zh-cn/) and locale-tagged mirrors such as
    python-docs-zh-tw, while leaving /en/ and canonical paths alone.
    """
    match = re.match(r"https?://([^/?#]+)(/[^?#]*)?", url or "", flags=re.I)
    if not match:
        return False
    tokens = [token for token in re.split(r"[.\-_/]+", f"{match.group(1)}{match.group(2) or ''}".lower()) if token]
    return any(token in LOCALE_SEGMENTS for token in tokens)


def apply_result_filters(
    rows: list[dict],
    *,
    drop_localized: bool,
    exclude_domains: list[str],
    dedupe_domain: bool,
    official_only: bool = False,
) -> tuple[list[dict], dict[str, int]]:
    """Apply local post-filters and report how many rows each one removed."""
    dropped = {"localized": 0, "excluded": 0, "not_official": 0, "duplicate": 0}
    excluded = {
        host
        for host in (normalize_site(domain).removeprefix("www.").removeprefix("m.") for domain in exclude_domains)
        if host
    }
    kept: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        url = row.get("url") or ""
        if drop_localized and is_localized(url):
            dropped["localized"] += 1
            continue
        host = url_host(url)
        if excluded and any(host == domain or host.endswith("." + domain) for domain in excluded):
            dropped["excluded"] += 1
            continue
        if official_only and not is_official_host(host):
            dropped["not_official"] += 1
            continue
        if dedupe_domain and host in seen:
            dropped["duplicate"] += 1
            continue
        seen.add(host)
        kept.append(row)
    return kept, dropped


def validate_search_args(args: argparse.Namespace) -> str:
    """Validate search arguments and return the final query string."""
    if not args.query or not args.query.strip():
        sys.exit("Error: 搜索词不能为空。")
    if not (1 <= args.count <= MAX_COUNT):
        sys.exit(f"Error: --count 需在 1~{MAX_COUNT} 之间。")
    if args.timeout <= 0:
        sys.exit("Error: --timeout 需大于 0。")
    if args.retries < 0:
        sys.exit("Error: --retries 不能为负数。")
    if args.content_preview < 0:
        sys.exit("Error: --content-preview 不能为负数。")
    if args.lang and not re.fullmatch(r"[a-z]{2,3}(,[a-z]{2,3})*", args.lang):
        sys.exit("Error: --lang 格式应为 en 或 zh,en。")
    for label, value in (("--after", args.after), ("--before", args.before)):
        if value and not re.fullmatch(r"\d{4}(-\d{2}-\d{2})?", value):
            sys.exit(f"Error: {label} 格式应为 YYYY 或 YYYY-MM-DD。")
    if args.localization:
        try:
            ipaddress.ip_address(args.localization)
        except ValueError:
            sys.exit("Error: --localization 需要合法 IP 地址。")
    if args.ori_question and len(args.ori_question) > MAX_QUERY_CHARS:
        sys.exit(f"Error: --ori-question 不能超过 {MAX_QUERY_CHARS} 字符。")
    query = build_query(args)
    if len(query) > MAX_QUERY_CHARS:
        sys.exit(f"Error: 拼接过滤条件后 query 为 {len(query)} 字符，超过 API 上限 {MAX_QUERY_CHARS}。请缩短查询词。")
    return query


# ── HTTP ──────────────────────────────────────────────────────────────


def request_json(
    path: str,
    payload: dict,
    *,
    api_key: str,
    base_url: str,
    timeout: int,
    retries: int,
) -> tuple[int, dict, int, int]:
    """POST JSON with retries on 408/429/5xx. Returns status, body, elapsed_ms, attempts."""
    url = f"{base_url.rstrip('/')}{path}"
    started = time.monotonic()
    last_error: Optional[str] = None
    for attempt in range(retries + 1):
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "deepseek-web-search-skill/1.0",
                },
                json=payload,
                timeout=timeout,
            )
        except requests.exceptions.Timeout:
            last_error = f"请求超时（{timeout}s）"
            if attempt < retries:
                time.sleep(min(2 ** attempt + random.random(), 6))
                continue
            raise
        except requests.exceptions.ConnectionError:
            last_error = "无法连接 api.deepseek.com"
            if attempt < retries:
                time.sleep(min(2 ** attempt + random.random(), 6))
                continue
            raise

        elapsed = round((time.monotonic() - started) * 1000)
        if response.status_code in RETRY_STATUS and attempt < retries:
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt + random.random(), 6)
            print(
                f"Warning: HTTP {response.status_code}，{delay:.1f}s 后重试 "
                f"({attempt + 1}/{retries})。",
                file=sys.stderr,
            )
            time.sleep(delay)
            continue

        try:
            body = response.json()
        except ValueError:
            body = {"error": {"message": response.text[:500] or "non-JSON response"}}
        return response.status_code, body, elapsed, attempt + 1

    raise RuntimeError(last_error or "request failed")


def error_message(body: dict) -> str:
    """Extract the human-readable message from an API error body."""
    error = body.get("error") if isinstance(body, dict) else None
    if isinstance(error, dict):
        return str(error.get("message") or error)
    return str(error or body)[:500]


def fail(status: int, body: dict) -> None:
    """Print an API failure with an actionable hint and exit."""
    message = error_message(body)
    hint = ERROR_HINTS.get(status, "请求失败。")
    print(f"Error (HTTP {status}): {message}", file=sys.stderr)
    print(f"Hint: {hint}", file=sys.stderr)
    sys.exit(1)


# ── Markdown cleanup ──────────────────────────────────────────────────

ESCAPED_PUNCT = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|>~/:,;'\"=])")
BOILERPLATE_LINES = {
    "skip to main content",
    "was this page helpful?",
    "responses are generated using ai and may contain mistakes.",
    "assistant",
    "fetch the complete documentation index at: /llms.txt",
    "use this file to discover all available pages before exploring further.",
    "documentation index",
}


def unescape_markdown(text: str) -> str:
    """Undo the backslash escaping applied by the Fetch extractor.

    The transform is heuristic: a literal `\\d` sequence survives, while an
    escaped regex `\\.` becomes `.`. Use --raw when exact backslashes matter.
    """
    return ESCAPED_PUNCT.sub(r"\1", text)


def clean_markdown(text: str) -> str:
    """Unescape and strip extractor boilerplate; returns readable Markdown."""
    text = unescape_markdown(text).replace("¶", "")
    lines = []
    for line in text.splitlines():
        if line.strip().lower() in BOILERPLATE_LINES:
            continue
        lines.append(line.rstrip())
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    """Truncate at a line boundary and append a marker; 0 means no limit."""
    if max_chars <= 0 or len(text) <= max_chars:
        return text, False
    cut = text.rfind("\n", 0, max_chars)
    if cut < max_chars // 2:
        cut = max_chars
    removed = len(text) - cut
    return f"{text[:cut].rstrip()}\n\n[... truncated {removed} chars; use --max-chars 0 for the full text]", True


# ── Output ────────────────────────────────────────────────────────────


def date_only(value: Optional[str]) -> str:
    """Return the date portion of an RFC 3339 timestamp."""
    return (value or "")[:10]


def format_search_human(body: dict, query: str, elapsed_ms: int, preview_chars: int,
                        quality: Optional[dict] = None) -> str:
    """Render search results for terminal reading."""
    rows = body.get("results") or []
    if not rows:
        return f"No results for: {query}\n({elapsed_ms}ms)"
    quality = quality or quality_summary(rows)
    header = f"results: {len(rows)} · {elapsed_ms}ms · official {quality['official_count']}/{len(rows)}"
    if quality["official_first_rank"] and not quality["official_top3"]:
        header += f" (first #{quality['official_first_rank']})"
    lines = [f"query: {query}", header, ""]
    for index, row in enumerate(rows, 1):
        authority = row.get("authority")
        score = row.get("rerank_score")
        host = url_host(row.get("url") or "")
        meta = [row.get("site_name") or "", date_only(row.get("date")),
                f"auth {authority}", f"rel {score:.2f}" if isinstance(score, (int, float)) else ""]
        if is_ip_host(host):
            meta.append("raw-ip")
        elif is_official_host(host):
            meta.append("official")
        lines.append(f"{index}. {row.get('title') or '(untitled)'}")
        lines.append(f"   {row.get('url') or ''}")
        lines.append("   " + " · ".join(item for item in meta if item))
        summary = (row.get("summary") or row.get("snippet") or "").replace("¶", "").strip()
        if summary:
            lines.append("   " + summary[:preview_chars].replace("\n", " "))
        content = row.get("content") or ""
        if content:
            preview = content[:preview_chars].replace("¶", "").replace(chr(10), " ")
            lines.append(f"   content: {len(content)} chars · {preview}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_search_json(body: dict, query: str, elapsed_ms: int, attempts: int,
                       quality: Optional[dict] = None) -> str:
    """Render a search response as stable JSON."""
    quality = quality or quality_summary(body.get("results") or [])
    return json.dumps(
        {
            "endpoint": ENDPOINTS["search"],
            "query": query,
            "elapsed_ms": elapsed_ms,
            "attempts": attempts,
            "quality": quality,
            "api_response": body,
        },
        ensure_ascii=False,
        indent=2,
    )


def format_fetch_json(title: str, content: str, url: str, elapsed_ms: int, attempts: int,
                      truncated: bool, raw: bool) -> str:
    """Render a fetch response as stable JSON."""
    return json.dumps(
        {
            "endpoint": ENDPOINTS["fetch"],
            "url": url,
            "title": title,
            "content": content,
            "chars": len(content),
            "truncated": truncated,
            "unescaped": not raw,
            "elapsed_ms": elapsed_ms,
            "attempts": attempts,
            "notes": [] if raw else FETCH_NOTES,
        },
        ensure_ascii=False,
        indent=2,
    )


# ── Commands ──────────────────────────────────────────────────────────


def command_search(args: argparse.Namespace) -> None:
    """Run a search request and print results."""
    query = validate_search_args(args)
    api_key = resolve_setting(args.api_key, API_KEY_ENV_NAMES)
    if not api_key:
        sys.exit(
            "Error: 未找到 DeepSeek API Key。任选一种方式配置：\n"
            "  1. export DEEPSEEK_API_KEY=sk-...\n"
            "  2. 命令行传入 --api-key sk-...\n"
            "  3. 在 skill 目录或当前目录的 .env 写入 DEEPSEEK_API_KEY=sk-...\n"
            "获取地址：https://platform.deepseek.com/api_keys"
        )
    base_url = resolve_setting(args.base_url, BASE_URL_ENV_NAMES) or DEFAULT_BASE_URL
    payload: dict = {"query": query, "count": args.count}
    if args.content:
        payload["need_content"] = True
    if args.ori_question:
        payload["ori_question"] = args.ori_question
    if args.localization:
        payload["localization"] = args.localization

    try:
        status, body, elapsed_ms, attempts = request_json(
            ENDPOINTS["search"], payload, api_key=api_key, base_url=base_url,
            timeout=args.timeout, retries=args.retries,
        )
    except requests.exceptions.Timeout:
        sys.exit(f"Error: 搜索请求超时（{args.timeout}s）。可加 --timeout 60 重试。")
    except requests.exceptions.ConnectionError:
        sys.exit("Error: 无法连接 api.deepseek.com，请检查网络或 DEEPSEEK_BASE_URL。")

    if status != 200:
        fail(status, body)

    rows = body.get("results") if isinstance(body, dict) else None
    quality = None
    if isinstance(rows, list):
        filtered, dropped = apply_result_filters(
            rows,
            drop_localized=args.drop_localized,
            exclude_domains=args.exclude_domains,
            dedupe_domain=args.dedupe_domain,
            official_only=args.official_only,
        )
        filtered = sort_rows(filtered, args.sort)
        removed = sum(dropped.values())
        if removed:
            detail = "，".join(f"{name} {count}" for name, count in dropped.items() if count)
            print(f"Filtered {removed} results（{detail}）。", file=sys.stderr)
        body = {**body, "results": filtered}
        quality = quality_summary(filtered, official_only=args.official_only)
        if quality["warning"]:
            print(f"Warning: {quality['warning']}", file=sys.stderr)

    if args.json:
        print(format_search_json(body, query, elapsed_ms, attempts, quality))
    else:
        print(format_search_human(body, query, elapsed_ms, args.content_preview, quality))


def command_fetch(args: argparse.Namespace) -> None:
    """Run a fetch request and print the page as Markdown."""
    url = args.url.strip()
    if not url:
        sys.exit("Error: 需要网页 URL。")
    if len(url) > MAX_URL_CHARS:
        sys.exit(f"Error: URL 超过 {MAX_URL_CHARS} 字符。")
    if not re.match(r"^https?://[^/?#\s]+", url, flags=re.I):
        sys.exit("Error: URL 必须是带 host 的 http/https 地址。")
    if args.timeout <= 0:
        sys.exit("Error: --timeout 需大于 0。")
    if args.retries < 0:
        sys.exit("Error: --retries 不能为负数。")
    if "@" in url.split("/", 3)[2]:
        sys.exit("Error: URL 不能携带用户名或密码。")

    api_key = resolve_setting(args.api_key, API_KEY_ENV_NAMES)
    if not api_key:
        sys.exit(
            "Error: 未找到 DeepSeek API Key。任选一种方式配置：\n"
            "  1. export DEEPSEEK_API_KEY=sk-...\n"
            "  2. 命令行传入 --api-key sk-...\n"
            "  3. 在 skill 目录或当前目录的 .env 写入 DEEPSEEK_API_KEY=sk-..."
        )
    base_url = resolve_setting(args.base_url, BASE_URL_ENV_NAMES) or DEFAULT_BASE_URL

    try:
        status, body, elapsed_ms, attempts = request_json(
            ENDPOINTS["fetch"], {"url": url}, api_key=api_key, base_url=base_url,
            timeout=args.timeout, retries=args.retries,
        )
    except requests.exceptions.Timeout:
        sys.exit(f"Error: 抓取超时（{args.timeout}s）。DeepSeek 对慢站点可能返回 504，建议加大 --timeout，或改用浏览器渲染的抓取工具。")
    except requests.exceptions.ConnectionError:
        sys.exit("Error: 无法连接 api.deepseek.com，请检查网络或 DEEPSEEK_BASE_URL。")

    if status != 200:
        fail(status, body)

    title = str(body.get("title") or "")
    raw_content = str(body.get("content") or "")
    content = raw_content if args.raw else clean_markdown(raw_content)
    content, truncated = truncate_text(content, args.max_chars)

    if args.output:
        path = Path(args.output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {len(content)} chars to {path}", file=sys.stderr)
        if not args.json:
            return

    if args.json:
        print(format_fetch_json(title, content, url, elapsed_ms, attempts, truncated, args.raw))
    else:
        if not args.raw:
            print("Note: 已反转义并清理正文；代码块、表格、链接目标会被抽取器压平。", file=sys.stderr)
        if title and not content.lstrip().startswith("#"):
            print(f"# {title}\n")
        print(content)


# ── CLI ───────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        prog="deepseek_search.py",
        description="DeepSeek Search / Fetch CLI (api.deepseek.com/v1/tools).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search the web and return ranked results.")
    search.add_argument("query", help="搜索词，≤128 字符；支持 site:、lang:、after:、before:、引号等语法。")
    search.add_argument("-c", "--count", type=int, default=DEFAULT_COUNT,
                        help=f"返回条数 1~{MAX_COUNT}（默认 {DEFAULT_COUNT}；>20 后长尾质量下降）。")
    search.add_argument("--content", action="store_true",
                        help="请求网页正文（need_content=true）。Search 返回的正文是未转义的干净 Markdown。")
    search.add_argument("--site", action="append", metavar="DOMAIN",
                        help="限定站点，可重复；多个站点用 OR 连接。示例：--site github.com --site huggingface.co")
    search.add_argument("--lang", metavar="CODES", help="限定语言，如 en 或 zh,en。英文技术查询建议加 --lang en。")
    search.add_argument("--after", metavar="DATE", help="只返回该日期之后发布的页面，YYYY 或 YYYY-MM-DD。")
    search.add_argument("--before", metavar="DATE", help="只返回该日期之前发布的页面，YYYY 或 YYYY-MM-DD。")
    search.add_argument("--drop-localized", action="store_true",
                        help="丢弃 /ja/、/zh-cn/、/pl/ 等本地化版本。英文技术查询建议开；会减少结果数。")
    search.add_argument("--exclude-domains", type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
                        default=[], metavar="DOMAINS",
                        help="逗号分隔的域名黑名单，如 csdn.net,sohu.com。")
    search.add_argument("--dedupe-domain", action="store_true",
                        help="同一域名只保留排名最高的一条，缓解门户站重复转载。")
    search.add_argument("--sort", choices=["rank", "official"], default="rank",
                        help="结果排序：rank 保持 API 相关性顺序（默认）；official 把官方/一手域移到前面，组内保持原序。")
    search.add_argument("--official-only", action="store_true",
                        help="只保留官方/一手域（gov/edu/ac、EU/WHO/IMF、arXiv/GitHub、厂商官方文档等）。为空时会提示改用 --site。")
    search.add_argument("--ori-question", metavar="TEXT", help="触发搜索的原始用户问题，帮助理解意图（≤128 字符）。")
    search.add_argument("--localization", metavar="IP", help="用于本地化排序的 IP 地址。")
    search.add_argument("--content-preview", type=int, default=DEFAULT_CONTENT_PREVIEW,
                        help=f"人类可读模式下正文预览字符数（默认 {DEFAULT_CONTENT_PREVIEW}）。")
    search.add_argument("--json", dest="json", action="store_true", help="输出结构化 JSON。")
    search.add_argument("--api-key", help="显式传入 API Key（默认读 DEEPSEEK_API_KEY / .env）。")
    search.add_argument("--base-url", help="覆盖 API Base URL（默认 https://api.deepseek.com）。")
    search.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"请求超时秒数（默认 {DEFAULT_TIMEOUT}）。")
    search.add_argument("--retries", type=int, default=2, help="408/429/5xx 重试次数（默认 2）。")
    search.set_defaults(func=command_search)

    fetch = subparsers.add_parser("fetch", help="Fetch a URL as Markdown.")
    fetch.add_argument("url", help="要抓取的 http/https URL（≤8192 字符）。")
    fetch.add_argument("--raw", action="store_true", help="保留原始转义内容，不做反转义和清理。")
    fetch.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                       help=f"输出截断上限（默认 {DEFAULT_MAX_CHARS}；0 表示不截断）。")
    fetch.add_argument("-o", "--output", help="写入文件而不是打印到 stdout。")
    fetch.add_argument("--json", dest="json", action="store_true", help="输出结构化 JSON。")
    fetch.add_argument("--api-key", help="显式传入 API Key（默认读 DEEPSEEK_API_KEY / .env）。")
    fetch.add_argument("--base-url", help="覆盖 API Base URL（默认 https://api.deepseek.com）。")
    fetch.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"请求超时秒数（默认 {DEFAULT_TIMEOUT}）。")
    fetch.add_argument("--retries", type=int, default=1, help="408/429/5xx 重试次数（默认 1；Fetch 重试成本高）。")
    fetch.set_defaults(func=command_fetch)

    return parser


def main() -> None:
    """Parse arguments and dispatch."""
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
