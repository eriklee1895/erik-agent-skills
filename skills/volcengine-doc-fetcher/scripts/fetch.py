#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "beautifulsoup4>=4.12",
#   "lxml>=5.0",
#   "markdownify>=1.1",
#   "playwright>=1.50",
# ]
# ///

"""
Fetch Volcano Engine (火山引擎) documentation pages as clean Markdown.

Three-tier strategy, cheapest first:

1. markdown  — native Markdown endpoints via curl + stdlib only, no browser:
   - ark.volcengine.com and console.volcengine.com/ark: append ".md" to the
     docs path; llms.txt / llms-full.txt / sitemap.xml / models.json pass through.
   - docs.volcengine.com / docs.byteplus.com doc-center: the browser URL
     "/docs/<product>/<slug>?lang=zh" does NOT accept a naive ".md" suffix;
     the canonical Markdown URL inserts a language segment,
     "/docs/zh/<product>/<slug>.md". The product llms.txt lists exact URLs.
   - legacy www.volcengine.com/docs/<product>/<doc> numeric URLs 301/302 to a
     doc-center canonical path, which is then transformed the same way.
2. playwright — headless Chromium rendering for pages without Markdown endpoints.
3. firecrawl  — CLI fallback when Playwright fails.

The heavy third-party imports (playwright, bs4, markdownify) are lazy, so tier 1
also runs under a plain python3 without installing the PEP 723 dependencies.

Usage:
    uv run scripts/fetch.py "https://ark.volcengine.com/region:cn-beijing/docs/overview"
    uv run scripts/fetch.py "https://docs.volcengine.com/docs/ark/quick-start-console?lang=zh"
    uv run scripts/fetch.py "https://www.volcengine.com/docs/6561/163032"
    uv run scripts/fetch.py --output-dir ./docs/ url1 url2 url3
    uv run scripts/fetch.py --method markdown --no-cache "https://..."
"""

import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

CACHE_DIR = Path.home() / ".cache" / "volcengine-docs"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "volcengine-doc-fetcher/2.0 (+markdown-native; curl)"
MARKDOWN_HOSTS = ("ark.volcengine.com", "docs.volcengine.com", "docs.byteplus.com")
PASSTHROUGH_SUFFIXES = (".txt", ".xml", ".json")

# CSS selector for the doc content area on legacy volcengine.com/docs pages.
# Uses fuzzy class matching because Volcengine uses CSS modules with hashed
# class names (e.g., "content-skqm contentdoc-wqiC").
CONTENT_SELECTOR = '[class*="content"][class*="doc"]'

# Noise selectors — DOM nodes to remove before Markdown conversion.
NOISE_SELECTORS = [
    ".breadcrumb-jjpG",          # Breadcrumb navigation
    ".btnBox-Vox6",              # Toolbar buttons (copy, download, favorite)
    ".primaryRow-pOm_",          # Toolbar row container
    ".toolbar-QUz9",             # Toolbar wrapper
    '[class*="feedback"]',       # "Was this page helpful?" widget
    ".doc-feedback",             # Alternative feedback class
    ".prev-next",                # Previous/Next navigation
    '[class*="prevNext"]',       # Alternative prev/next class
    ".ask-ai",                   # "Ask AI assistant" button
    '[class*="askAi"]',          # Alternative ask AI class
]


# --------------------------------------------------------------------------- #
# URL routing
# --------------------------------------------------------------------------- #

def _strip_query(url: str) -> str:
    return url.split("?", 1)[0].split("#", 1)[0]


def resolve_native_markdown(url: str) -> Optional[str]:
    """Map a browser/doc URL to its native Markdown URL, or None if impossible.

    Returns the exact URL to GET. Only covers verified host patterns; unknown
    hosts return None so callers fall through to browser rendering.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path
    query = parsed.query

    # Tier 1a: Ark doc platform — both ark.volcengine.com and the
    # console.volcengine.com/ark mirror serve the same ".md" objects.
    if host == "ark.volcengine.com" or (
        host == "console.volcengine.com" and path.startswith("/ark/")
    ):
        if path.endswith(PASSTHROUGH_SUFFIXES):
            return _strip_query(url)
        if path.endswith(".md"):
            return _strip_query(url)
        if "/docs/" in path:
            return f"{parsed.scheme}://{host}{path}.md"
        return None

    # Tier 1b: unified doc center (docs.volcengine.com / docs.byteplus.com).
    if host in ("docs.volcengine.com", "docs.byteplus.com"):
        if path.endswith(PASSTHROUGH_SUFFIXES):
            return _strip_query(url)
        clean = _strip_query(url)
        if clean.endswith(".md"):
            return clean

        # /docs/<lang>/<product>/<slug> already carries a language segment.
        m = re.match(r"^/docs/(zh|en)/(.+)$", path)
        if m:
            lang, rest = m.groups()
            return f"{parsed.scheme}://{host}/docs/{lang}/{rest}.md"

        # Browser form: /docs/<product>/<slug>[?lang=zh]. Insert the language
        # segment; byteplus defaults to English, volcengine to Chinese.
        m = re.match(r"^/docs/([^/]+)/([^/]+)$", path)
        if m:
            lang = "en" if host == "docs.byteplus.com" else "zh"
            qs_lang = re.search(r"[?&]lang=([a-z]{2})", query)
            if qs_lang:
                lang = qs_lang.group(1)
            product, slug = m.groups()
            return f"{parsed.scheme}://{host}/docs/{lang}/{product}/{slug}.md"
        return None

    # Tier 1c: legacy numeric URLs redirect to doc-center canonical paths.
    # Resolving the redirect itself requires a (cheap, no-browser) HTTP hop;
    # callers do that in resolve_legacy_redirect().
    if host == "www.volcengine.com" and re.match(r"^/docs/\d+/\d+", path):
        return "LEGACY_REDIRECT"

    return None


def resolve_legacy_redirect(url: str, timeout: int) -> Optional[str]:
    """Follow a legacy www.volcengine.com numeric URL to its doc-center target.

    The redirect chain lands on a docs.volcengine.com browser URL, which is then
    transformed to its canonical Markdown URL. Returns None on any failure.
    """
    try:
        _, _, _, effective = curl_get(url, timeout)
    except RuntimeError:
        return None

    if urlparse(effective).netloc not in ("docs.volcengine.com", "docs.byteplus.com"):
        return None
    return resolve_native_markdown(effective)


# --------------------------------------------------------------------------- #
# Cache and slugs
# --------------------------------------------------------------------------- #

def url_to_slug(url: str) -> str:
    """Derive a filesystem-safe slug from any supported doc URL."""
    parsed = urlparse(url)
    path = parsed.path

    # Legacy numeric docs: 6561-163032
    m = re.search(r"/docs/(\d+)/(\d+)", path)
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    # Ark / doc-center pages use word slugs; combine the last two segments to
    # avoid collisions (e.g. .../ark/overview vs .../other/overview).
    segments = [s for s in path.split("/") if s]
    if segments:
        tail = "-".join(segments[-2:])
        tail = re.sub(r"[^A-Za-z0-9._-]", "-", tail)
        if tail:
            return tail[:80]
    return hashlib.md5(url.encode()).hexdigest()[:12]


def cache_path(url: str) -> tuple[Path, Path]:
    slug = url_to_slug(url)
    return CACHE_DIR / f"{slug}.md", CACHE_DIR / f"{slug}.meta.json"


def read_cache(url: str, ttl: int) -> Optional[dict]:
    md_path, meta_path = cache_path(url)
    if not md_path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text())
        if time.time() - meta.get("fetched_at", 0) > ttl:
            return None
        return {
            "markdown": md_path.read_text(),
            "title": meta.get("title", ""),
            "method": meta.get("method", "cached"),
            "cached": True,
            "fetched_at": meta.get("fetched_at", ""),
        }
    except (json.JSONDecodeError, OSError):
        return None


def write_cache(url: str, result: dict) -> None:
    md_path, meta_path = cache_path(url)
    md_path.write_text(result["markdown"])
    meta = {
        "url": url,
        "title": result.get("title", ""),
        "method": result.get("method", ""),
        "fetched_at": result.get("fetched_at", time.time()),
        "slug": url_to_slug(url),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))


# --------------------------------------------------------------------------- #
# Tier 1: native Markdown over curl
# --------------------------------------------------------------------------- #

def normalize_native_markdown(raw: str) -> str:
    """Light cleanup for already-Markdown payloads (BOM, blank lines)."""
    text = raw.lstrip("\ufeff")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip() + "\n"


def curl_get(url: str, timeout: int) -> tuple[int, str, str, str]:
    """GET following redirects via curl (system trust store handles MITM proxies).

    Returns (http_status, content_type, decoded_body, effective_url).
    Raises RuntimeError on transport failure.
    """
    proc = subprocess.run(
        [
            "curl", "-sS", "-L", "--max-time", str(timeout),
            "-H", f"User-Agent: {USER_AGENT}",
            "-H", "Accept: text/markdown, text/plain, */*",
            "-w", "\n%{http_code}\t%{content_type}\t%{url_effective}",
            url,
        ],
        capture_output=True,
        timeout=timeout + 15,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed: {proc.stderr.decode('utf-8', 'replace').strip()}")

    payload = proc.stdout.decode("utf-8", errors="replace")
    body, _, trailer = payload.rpartition("\n")
    try:
        status_s, content_type, effective = trailer.split("\t", 2)
        return int(status_s), content_type, body, effective
    except ValueError as e:
        raise RuntimeError(f"unparseable curl trailer: {trailer!r}") from e


def fetch_native_markdown(url: str, timeout: int) -> dict:
    """GET a native Markdown object. Raises on non-200/non-Markdown responses."""
    status, content_type, raw, _ = curl_get(url, timeout)
    if status != 200:
        raise RuntimeError(f"native markdown HTTP {status}")
    # A 404 on doc-center returns JSON; an SPA fallback returns HTML. Both mean
    # the Markdown endpoint does not exist for this URL.
    if "text/markdown" not in content_type and "text/plain" not in content_type:
        raise RuntimeError(f"native markdown unexpected content-type: {content_type}")

    markdown = normalize_native_markdown(raw)
    if not markdown.strip():
        raise RuntimeError("native markdown returned empty body")

    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return {
        "markdown": markdown,
        "title": title_match.group(1).strip() if title_match else "",
        "method": "markdown",
        "cached": False,
        "fetched_at": time.time(),
    }


# --------------------------------------------------------------------------- #
# Tier 2/3: browser rendering (legacy behavior, lazy heavy imports)
# --------------------------------------------------------------------------- #

def clean_html(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    for selector in NOISE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()
    return str(soup)


def html_to_markdown(html: str) -> str:
    from markdownify import markdownify as md

    markdown = md(html, heading_style="ATX")
    markdown = re.sub(r"​", "", markdown)
    markdown = re.sub(r"!\[.*?\]\(data:image/[^)]+\)", "", markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    lines = [line.rstrip() for line in markdown.splitlines()]
    return "\n".join(lines).strip() + "\n"


async def fetch_playwright(url: str, timeout: int) -> dict:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)

            title = await page.title()
            title = re.sub(r"--火山引擎$", "", title).strip()

            content_el = await page.query_selector(CONTENT_SELECTOR)
            if not content_el:
                raise ValueError(
                    f"Could not find doc content area with selector: {CONTENT_SELECTOR}"
                )

            html = await page.evaluate("el => el.innerHTML", content_el)
            markdown = html_to_markdown(clean_html(html))
            if not markdown.strip():
                raise ValueError("Extracted content is empty")

            return {
                "markdown": markdown,
                "title": title,
                "method": "playwright",
                "cached": False,
                "fetched_at": time.time(),
            }
        finally:
            await browser.close()


def fetch_firecrawl(url: str) -> dict:
    result = subprocess.run(
        [
            "firecrawl",
            "scrape",
            url,
            "--only-main-content",
            "--wait-for",
            "5000",
            "--format",
            "markdown",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Firecrawl failed: {result.stderr.strip()}")

    markdown = result.stdout.strip()
    if not markdown:
        raise ValueError("Firecrawl returned empty content")

    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return {
        "markdown": markdown + "\n",
        "title": title_match.group(1).strip() if title_match else "",
        "method": "firecrawl",
        "cached": False,
        "fetched_at": time.time(),
    }


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

async def fetch_single(
    url: str,
    method: str = "auto",
    timeout: int = 30,
    use_cache: bool = True,
    cache_ttl: int = 3600,
) -> dict:
    """Fetch one URL. Result dict has url + markdown/title/method/cached, or url + error."""
    if use_cache:
        cached = read_cache(url, cache_ttl)
        if cached:
            cached["url"] = url
            return cached

    errors: list[str] = []

    # Tier 1: native Markdown (curl + stdlib only). Blocking curl runs in a
    # thread so the asyncio concurrency cap keeps working across tiers.
    if method in ("auto", "markdown"):
        try:
            native_url = resolve_native_markdown(url)
            if native_url == "LEGACY_REDIRECT":
                native_url = await asyncio.to_thread(resolve_legacy_redirect, url, timeout)
            if native_url:
                result = await asyncio.to_thread(fetch_native_markdown, native_url, timeout)
                result["url"] = url
                if use_cache:
                    write_cache(url, result)
                return result
            if method == "markdown":
                return {"url": url, "error": "No native Markdown endpoint matches this URL"}
        except Exception as e:
            errors.append(f"Markdown: {e}")
            if method == "markdown":
                return {"url": url, "error": f"Markdown failed: {e}"}

    # Tier 2: Playwright.
    if method in ("auto", "playwright"):
        try:
            result = await fetch_playwright(url, timeout)
            result["url"] = url
            if use_cache:
                write_cache(url, result)
            return result
        except Exception as e:
            errors.append(f"Playwright: {e}")
            if method == "playwright":
                return {"url": url, "error": f"Playwright failed: {e}"}

    # Tier 3: Firecrawl.
    if method in ("auto", "firecrawl"):
        if method == "auto" and errors:
            print(
                f"⚠️  Native/Playwright unavailable, falling back to Firecrawl: {errors[-1]}",
                file=sys.stderr,
            )
        try:
            result = await asyncio.to_thread(fetch_firecrawl, url)
            result["url"] = url
            if use_cache:
                write_cache(url, result)
            return result
        except Exception as e:
            errors.append(f"Firecrawl: {e}")
            return {"url": url, "error": "All methods failed: " + "; ".join(errors)}

    return {"url": url, "error": f"Unknown method: {method}"}


async def fetch_multiple(
    urls: list[str],
    method: str = "auto",
    timeout: int = 30,
    concurrency: int = 3,
    use_cache: bool = True,
    cache_ttl: int = 3600,
) -> list[dict]:
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_fetch(u: str) -> dict:
        async with semaphore:
            return await fetch_single(u, method, timeout, use_cache, cache_ttl)

    return await asyncio.gather(*(bounded_fetch(u) for u in urls))


def output_stdout(results: list[dict], json_mode: bool = False) -> None:
    if json_mode:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    for i, result in enumerate(results):
        if "error" in result:
            print(f"# Error: {result['url']}\n\n{result['error']}\n")
        else:
            if result.get("title"):
                print(f"# {result['title']}\n")
            print(result["markdown"])
        if i < len(results) - 1:
            print("---\n")


def output_files(results: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        slug = url_to_slug(result["url"])
        if "error" in result:
            print(f"⚠️  {slug}: {result['error']}", file=sys.stderr)
            continue

        (output_dir / f"{slug}.md").write_text(result["markdown"])
        meta = {
            "url": result["url"],
            "title": result.get("title", ""),
            "method": result.get("method", ""),
            "cached": result.get("cached", False),
            "fetched_at": result.get("fetched_at", time.time()),
            "slug": slug,
        }
        (output_dir / f"{slug}.meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2)
        )
        print(f"✓ {slug}.md ({result.get('method', 'unknown')})")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Volcano Engine documentation pages as clean Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/fetch.py "https://ark.volcengine.com/region:cn-beijing/docs/overview"
  uv run scripts/fetch.py "https://docs.volcengine.com/docs/ark/quick-start-console?lang=zh"
  uv run scripts/fetch.py "https://www.volcengine.com/docs/6561/163032"
  uv run scripts/fetch.py --output-dir ./docs/ url1 url2 url3
  uv run scripts/fetch.py --method markdown --no-cache "https://..."
        """,
    )
    parser.add_argument("urls", nargs="+", help="One or more Volcano Engine doc URLs to fetch")
    parser.add_argument(
        "--method",
        choices=["auto", "markdown", "playwright", "firecrawl"],
        default="auto",
        help="auto (native Markdown, then Playwright, then Firecrawl); "
        "markdown (native endpoints only, no browser); playwright; firecrawl. Default: auto",
    )
    parser.add_argument(
        "--output-dir", "-o", type=Path, default=None,
        help="Save output to directory instead of stdout. Each URL gets {slug}.md and {slug}.meta.json",
    )
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache, force re-fetch")
    parser.add_argument(
        "--cache-ttl", type=int, default=3600,
        help="Cache TTL in seconds (default: 3600 = 1 hour)",
    )
    parser.add_argument(
        "--concurrency", "-c", type=int, default=3,
        help="Max concurrent fetches for multi-URL (default: 3)",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout instead of Markdown")
    parser.add_argument(
        "--timeout", type=int, default=30,
        help="Per-request timeout in seconds (default: 30)",
    )

    args = parser.parse_args()
    results = asyncio.run(
        fetch_multiple(
            args.urls,
            method=args.method,
            timeout=args.timeout,
            concurrency=args.concurrency,
            use_cache=not args.no_cache,
            cache_ttl=args.cache_ttl,
        )
    )

    if args.output_dir:
        output_files(results, args.output_dir)
    else:
        output_stdout(results, json_mode=args.json)

    if any("error" in r for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
