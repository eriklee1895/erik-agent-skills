#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests>=2.32",
# ]
# ///
"""
volcengine-web-search — Volcano Engine Doubao Search (豆包搜索) CLI.

豆包搜索（原名「联网搜索 / 融合信息搜索」）分为两个版本：

- Custom 版（默认）：低时延（~700ms），支持时间/域名/权威度/行业过滤、
  正文返回、订阅套餐 Key，web 最多 50 条。
  Endpoint: /search_api/web_search
- Global 版：覆盖全球站点、摘要长度可控、支持图搜图（visual），
  web/image 最多 20 条。仅支持按量后付费 Key。
  Endpoint: /search_api/global_search

搜索类型：
- web    文搜文（两个版本均支持）
- image  文搜图（两个版本均支持）
- visual 图搜图（仅 Global 版，需 --image-url 或 --image-file）

Examples:
    uv run search.py "北京三日游攻略" --json
    uv run search.py "latest AI research" --global --count 10 --max-snippet-length 1000
    uv run search.py "故宫雪景" --type image --orientation landscape --min-short-edge 1080
    uv run search.py "新能源汽车政策" --industry gov --authoritative-only
    uv run search.py "国内新能源汽车政策" --global --icp-host-only
    uv run search.py --type visual --image-url https://example.com/product.jpg --global
    uv run search.py --type visual --image-file ./shot.png --roi 0.1,0.2,0.7,0.9 --global
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests

# ── Constants ─────────────────────────────────────────────────────────

ENDPOINTS = {
    "custom": "https://open.feedcoopapi.com/search_api/web_search",
    "global": "https://open.feedcoopapi.com/search_api/global_search",
}
TRAFFIC_TAG_HEADER = "X-Traffic-Tag"
TRAFFIC_TAG_VALUE = "skill_web_search_common"

DEFAULT_COUNT = 10
CUSTOM_MAX_WEB_COUNT = 50
CUSTOM_MAX_IMAGE_COUNT = 5
GLOBAL_MAX_COUNT = 20

SUMMARY_PREVIEW_LIMIT = 800
# 如意卡片结果本身就是渲染好的结构化答案（天气/汇率/赛程等），人类输出多展示一些
RUYI_PREVIEW_LIMIT = 1800
MAX_SNIPPET_LENGTH_CAP = 3000
MAX_IMAGES_PER_DOC_CAP = 10

TIME_RANGE_MAP = {
    "day": "OneDay",
    "week": "OneWeek",
    "month": "OneMonth",
    "year": "OneYear",
}
TIME_RANGE_SHORTCUTS = {"OneDay", "OneWeek", "OneMonth", "OneYear"}
DATE_RANGE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$")

# Global 版宽高比定义为 height / width
ORIENTATION_ASPECT = {
    "landscape": {"AspectRatioMax": 0.85},
    "portrait": {"AspectRatioMin": 1.18},
    "square": {"AspectRatioMin": 0.85, "AspectRatioMax": 1.18},
}
ORIENTATION_SHAPE = {
    "landscape": ["横长方形"],
    "portrait": ["竖长方形"],
    "square": ["方形"],
}

AUTHORITY_LABEL = {"very_high": "非常权威", "high": "正常权威", "normal": "一般权威"}

# 错误码 → 处理建议（Custom 与 Global 合并，不适用的码不会出现）
ERROR_HINTS = {
    "invalid_api_key": "API Key 无效。请确认 Key 来自豆包搜索控制台（而非火山方舟 Ark），且没有多余空格。",
    "700901": "APIKey 无效（Global 版）。检查 Authorization Header 是否为 Bearer <APIKey>，Key 是否来自按量后付费。",
    "10400": "参数错误：检查 Query 是否为空、字段类型是否正确；图搜图请确认传了 --image-url/--image-file。",
    "10401": "TOP 网关 Token 无效（AK/SK 接入）：检查 Token 是否正确。",
    "10402": "搜索类型非法或未开通：检查 --type（web/image/visual），并确认控制台已开通对应搜索类型。",
    "10403": "权限错误：确认账号已开通豆包搜索服务、Key 与版本匹配（订阅套餐 Key 仅支持 Custom 版 web/image）。",
    "10406": "每月 500 次免费额度已用尽：到控制台开通按量后付费，或购买订阅套餐。",
    "10407": "当前无可用免费策略：检查账户状态或联系支持。",
    "10408": "服务未付费开通或账户欠费：请在控制台开通付费/充值（欠费 24h 内充值可恢复）。",
    "10409": "套餐模式不支持：订阅套餐 Key 不能调用 Global 版（global_search），Global 仅支持按量后付费 Key；请换用「按量后付费」标签页创建的 Key。",
    "10410": "无可用订阅套餐：套餐可能未开通或已到期，检查控制台套餐状态。",
    "10412": "套餐额度不足：升配套餐或换用按量后付费 Key。",
    "10500": "服务内部错误：等待几秒后重试；持续失败请携带 RequestId 联系支持。",
    "10501": "免费额度链路依赖失败（Global 版）：可重试；持续失败请携带 RequestId 排查。",
    "700429": "触发 QPS 限流（默认 10 QPS）：降低并发后重试；批量调用可加 --queue 开启队列模式。",
    "100013": "子账号未授权：主账号需为子账号添加 TorchlightApiFullAccess 权限。",
}

API_KEY_ENV_NAMES = [
    "VOLC_WEB_SEARCH_API_KEY",  # 本 skill 原有变量名
    "WEB_SEARCH_API_KEY",       # 官方 skill / 文档使用
    "ASK_ECHO_SEARCH_INFINITY_API_KEY",  # 官方 MCP server 使用
]


# ── API key resolution ────────────────────────────────────────────────


def load_env_file(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict, ignoring comments and blank lines."""
    env: dict[str, str] = {}
    if not path.is_file():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip("\"'")
    return env


def resolve_api_key(cli_key: Optional[str]) -> Optional[str]:
    """Resolve API key in priority order:
    1. --api-key CLI argument
    2. Environment variables (VOLC_WEB_SEARCH_API_KEY, WEB_SEARCH_API_KEY,
       ASK_ECHO_SEARCH_INFINITY_API_KEY)
    3. .env file in the script directory
    4. .env file in the current working directory
    """
    if cli_key:
        return cli_key.strip()

    for name in API_KEY_ENV_NAMES:
        value = os.environ.get(name)
        if value:
            return value.strip()

    for env_path in (Path(__file__).resolve().parent.parent / ".env", Path.cwd() / ".env"):
        file_env = load_env_file(env_path)
        for name in API_KEY_ENV_NAMES:
            if file_env.get(name):
                return file_env[name].strip()

    return None


# ── Time range ────────────────────────────────────────────────────────


def normalize_time_range(value: Optional[str]) -> Optional[str]:
    """Convert CLI-friendly time range to the API's OneX / date-range form."""
    if value is None:
        return None
    lowered = value.lower()
    if lowered in TIME_RANGE_MAP:
        return TIME_RANGE_MAP[lowered]
    if value in TIME_RANGE_SHORTCUTS:
        return value
    if DATE_RANGE_PATTERN.match(value):
        return value
    sys.exit(
        "Error: --time-range 需为 day/week/month/year、OneDay/OneWeek/OneMonth/OneYear，"
        "或日期区间 YYYY-MM-DD..YYYY-MM-DD。"
    )


# ── Payload builders ──────────────────────────────────────────────────


def build_custom_payload(args: argparse.Namespace) -> dict:
    """Build request body for the Custom edition (/search_api/web_search)."""
    payload: dict = {
        "Query": args.query,
        "SearchType": args.search_type,
        "Count": args.count,
    }

    filters: dict = {}
    if args.sites:
        filters["Sites"] = args.sites
    if args.block_sites:
        filters["BlockHosts"] = args.block_sites
    if args.authoritative_only:
        filters["AuthInfoLevel"] = 1
    if args.search_type == "web" and args.need_content:
        # Filter.NeedContent：仅返回有正文的结果（Content/Summary 默认即返回）
        filters["NeedContent"] = True
    if args.search_type == "image":
        if args.orientation:
            filters["ImageShapes"] = ORIENTATION_SHAPE[args.orientation]
        if args.min_short_edge:
            # Custom 版只有独立的宽/高下限，这里近似表达「短边不小于」
            filters["ImageWidthMin"] = args.min_short_edge
            filters["ImageHeightMin"] = args.min_short_edge
    if filters:
        payload["Filter"] = filters

    if args.search_type == "web":
        if args.content_format:
            payload["ContentFormats"] = args.content_format
        if args.industry:
            payload["Industry"] = args.industry
        if args.time_range:
            payload["TimeRange"] = args.time_range

    if args.query_rewrite:
        payload["QueryControl"] = {"QueryRewrite": True}

    if args.queue:
        payload["EnableWaiting"] = True
        payload["MaxWaitTime"] = 10000

    return payload


def build_global_payload(args: argparse.Namespace) -> dict:
    """Build request body for the Global edition (/search_api/global_search)."""
    payload: dict = {
        "Query": args.query or "",
        "SearchType": args.search_type,
        "DocCount": args.count,
    }

    if args.max_snippet_length:
        payload["MaxSnippetLength"] = min(args.max_snippet_length, MAX_SNIPPET_LENGTH_CAP)
    if args.max_images_per_doc:
        payload["MaxImageCountPerDoc"] = min(args.max_images_per_doc, MAX_IMAGES_PER_DOC_CAP)
    if args.icp_host_only:
        payload["Filter"] = {"IcpHostOnly": True}

    if args.search_type == "image":
        image_filter: dict = {}
        if args.min_short_edge:
            image_filter["ShortEdgePixelMin"] = args.min_short_edge
        if args.orientation:
            image_filter.update(ORIENTATION_ASPECT[args.orientation])
        if image_filter:
            payload["ImageFilter"] = image_filter

    if args.search_type == "visual":
        image_query: dict = {}
        if args.image_url:
            image_query["Url"] = args.image_url
        else:
            image_query["ImageBase64"] = encode_image_file(args.image_file)
        if args.roi:
            xmin, ymin, xmax, ymax = args.roi
            image_query["RegionOfInterest"] = {
                "XMin": xmin,
                "YMin": ymin,
                "XMax": xmax,
                "YMax": ymax,
            }
        payload["ImageQuery"] = image_query

    if args.queue:
        payload["EnableWaiting"] = True
        payload["MaxWaitTime"] = 10000

    return payload


def encode_image_file(path_str: str) -> str:
    """Read a local image file and return pure base64 (no data URL prefix)."""
    path = Path(path_str)
    if not path.is_file():
        sys.exit(f"Error: 图片文件不存在: {path}")
    mime = mimetypes.guess_type(path.name)[0]
    if mime and not mime.startswith("image/"):
        sys.exit(f"Error: {path} 不是图片文件（检测到 {mime}）")
    return base64.b64encode(path.read_bytes()).decode("ascii")


# ── API call ──────────────────────────────────────────────────────────


def call_search(edition: str, api_key: str, payload: dict, timeout: int = 60) -> dict:
    """POST the search request and return the parsed JSON response."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        TRAFFIC_TAG_HEADER: TRAFFIC_TAG_VALUE,
    }
    response = requests.post(
        ENDPOINTS[edition], json=payload, headers=headers, timeout=timeout
    )

    try:
        data = response.json()
    except ValueError:
        sys.exit(f"Error: 响应不是合法 JSON（HTTP {response.status_code}）：{response.text[:300]}")

    if response.status_code >= 400:
        meta_error = (data.get("ResponseMetadata") or {}).get("Error") or {}
        code = str(meta_error.get("Code") or response.status_code)
        message = meta_error.get("Message") or response.text[:500]
        if response.status_code >= 500 and code == str(response.status_code):
            # 服务端无结构化错误码（如 Global 版过滤条件互相矛盾导致空召回）
            message = f"{message}（服务端错误，可直接重试；若使用了互相矛盾的过滤条件，如 site: 海外站点 + --icp-host-only，请调整后重试）"
        fail_with_api_error(code, message)

    # 接口层错误（两个版本通用）
    meta_error = (data.get("ResponseMetadata") or {}).get("Error")
    if meta_error:
        fail_with_api_error(str(meta_error.get("Code", "unknown")), meta_error.get("Message", ""))

    # Global 版业务错误放在 Result.ErrorCode / ErrorMsg
    result = data.get("Result")
    if isinstance(result, dict) and result.get("ErrorCode") not in (None, 0):
        fail_with_api_error(str(result.get("ErrorCode")), result.get("ErrorMsg", ""))

    return data


def fail_with_api_error(code: str, message: str):
    hint = ERROR_HINTS.get(code)
    lines = [f"API error [{code}]: {message}"]
    if hint:
        lines.append(f"提示：{hint}")
    if code in ("invalid_api_key", "700901", "10403"):
        lines.append(
            "获取 Key：https://console.volcengine.com/search-infinity/api-key"
            "（订阅套餐 Key 与按量后付费 Key 相互隔离；Global 版仅支持按量后付费 Key）"
        )
    sys.exit("\n".join(lines))


# ── Human-readable formatters ─────────────────────────────────────────


def format_custom_human(data: dict, search_type: str, elapsed: float) -> str:
    result = data.get("Result") or {}
    count = result.get("ResultCount", 0)
    query = (result.get("SearchContext") or {}).get("OriginQuery", "")
    lines = [f"🔍 搜索: \"{query}\" ({count} 条结果, {elapsed:.1f}s, Custom 版)\n"]

    if search_type == "image":
        for i, item in enumerate(result.get("ImageResults") or [], 1):
            image = item.get("Image") or {}
            features = image.get("Features") or {}
            lines.append(f"{i}. {item.get('Title', '无标题')}")
            meta = [
                f"📎 {item.get('SiteName', '?')}",
                f"📐 {image.get('Width', '?')}×{image.get('Height', '?')} {image.get('Shape', '')}".rstrip(),
                f"🎯 {image.get('BlurDes', '?')}",
            ]
            if features.get("Description"):
                meta.append(features["Description"])
            lines.append(f"   {' | '.join(meta)}")
            if image.get("Url"):
                lines.append(f"   🔗 {image['Url']}")
            lines.append("")
        return "\n".join(lines)

    for i, item in enumerate(result.get("WebResults") or [], 1):
        score = item.get("RankScore") or 0
        published = item.get("PublishTime", "")[:10] if item.get("PublishTime") else None
        authority = item.get("AuthInfoDes", "")
        ruyi = (item.get("RuyiInfo") or {}).get("Type")

        lines.append(f"{i}. {item.get('Title', '无标题')}")
        meta_parts = [f"📎 {item.get('SiteName', '?')}"]
        if published:
            meta_parts.append(f"🕐 {published}")
        if score:
            meta_parts.append(f"⭐ {score:.2f}")
        if authority:
            meta_parts.append(f"🏛 {authority}")
        if ruyi:
            meta_parts.append(f"🎴 如意卡片:{ruyi}")
        lines.append(f"   {' | '.join(meta_parts)}")

        # 如意卡片结果：Content/Summary 就是渲染好的结构化答案，优先且多展示
        if ruyi:
            body = item.get("Content") or item.get("Summary") or item.get("Snippet", "")
            cap = RUYI_PREVIEW_LIMIT
        else:
            body = item.get("Summary") or item.get("Snippet", "")
            cap = SUMMARY_PREVIEW_LIMIT
        if body:
            truncated = body[:cap]
            if len(body) > cap:
                truncated += "…（--json 查看全文）"
            lines.append(f"   {truncated}")

        inline_images = item.get("InlineImages") or []
        for img in inline_images[:3]:
            alt = f" — {img['Alt']}" if img.get("Alt") else ""
            lines.append(f"   🖼 {img.get('ImageUrl', '')}{alt}")

        if item.get("Url"):
            lines.append(f"   🔗 {item['Url']}")
        lines.append("")

    return "\n".join(lines)


def format_global_human(data: dict, search_type: str, elapsed: float) -> str:
    result = data.get("Result") or {}
    total = result.get("TotalDocCount", 0)
    documents = result.get("Documents") or []
    label = {"web": "文搜文", "image": "文搜图", "visual": "图搜图"}.get(search_type, search_type)
    lines = [
        f"🔍 搜索: \"{data.get('_query', '')}\" "
        f"({len(documents)} 条返回 / 共 {total} 条可检索, {elapsed:.1f}s, Global 版 · {label})\n"
    ]

    for doc in documents:
        rank = doc.get("Rank", 0) + 1
        host_info = doc.get("HostInfo") or {}
        doc_info = doc.get("DocumentInfo") or {}
        authority = AUTHORITY_LABEL.get(host_info.get("AuthorityLevel", ""), "")
        published = doc_info.get("PublishTime") or ""
        published = published[:10] if published else None

        lines.append(f"{rank}. {doc.get('Title', '无标题')}")
        meta_parts = [f"📎 {host_info.get('Hostname', '?')}"]
        if published:
            meta_parts.append(f"🕐 {published}")
        if doc_info.get("Filetype"):
            meta_parts.append(f"📄 {doc_info['Filetype']}")
        if authority:
            meta_parts.append(f"🏛 {authority}")
        lines.append(f"   {' | '.join(meta_parts)}")

        text_parts = []
        image_count = 0
        for snippet in doc.get("Snippet") or []:
            if snippet.get("Type") == "text" and snippet.get("Text"):
                text_parts.append(snippet["Text"].strip())
            elif snippet.get("Type") == "image":
                image = snippet.get("Image") or {}
                # 只把带 URL 的图片计入展示上限，避免无链接片段挤占名额
                if not image.get("ImageUrl"):
                    continue
                image_count += 1
                if image_count <= 3:
                    alt = f" — {image['Alt']}" if image.get("Alt") else ""
                    size = f" ({image.get('Width', '?')}×{image.get('Height', '?')})"
                    lines.append(f"   🖼 {image['ImageUrl']}{size}{alt}")

        combined = "\n".join(text_parts).strip()
        if combined:
            truncated = combined[:SUMMARY_PREVIEW_LIMIT]
            if len(combined) > SUMMARY_PREVIEW_LIMIT:
                truncated += "…"
            lines.append(f"   {truncated}")
        if image_count > 3:
            lines.append(f"   🖼 …另有 {image_count - 3} 张图片（--json 查看全部）")

        if doc.get("Url"):
            lines.append(f"   🔗 {doc['Url']}")
        lines.append("")

    return "\n".join(lines)


def format_json(data: dict, elapsed: float, edition: str, search_type: str) -> str:
    output = {
        "elapsed_ms": int(elapsed * 1000),
        "edition": edition,
        "search_type": search_type,
        "api_response": data,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


# ── CLI ───────────────────────────────────────────────────────────────

CUSTOM_ONLY_FLAGS = [
    ("time_range", "--time-range", "时间过滤"),
    ("sites", "--sites", "指定域名"),
    ("block_sites", "--block-sites", "屏蔽域名"),
    ("authoritative_only", "--authoritative-only", "权威来源过滤"),
    ("industry", "--industry", "行业搜索"),
    ("need_content", "--need-content", "正文返回"),
    ("content_format", "--content-format", "正文格式"),
    ("query_rewrite", "--query-rewrite", "Query 改写"),
]
GLOBAL_ONLY_FLAGS = [
    ("icp_host_only", "--icp-host-only", "ICP 备案站点过滤"),
    ("max_snippet_length", "--max-snippet-length", "摘要长度控制"),
    ("max_images_per_doc", "--max-images-per-doc", "每条结果图片数"),
    ("image_url", "--image-url", "图搜图"),
    ("image_file", "--image-file", "图搜图"),
    ("roi", "--roi", "图搜图子区域"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="volcengine-web-search",
        description="豆包搜索（Doubao Search）CLI：Custom 版（默认，低时延、过滤丰富）与 Global 版（全球站点、图搜图）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run search.py "北京三日游攻略" --json
  uv run search.py "OpenAI 最新发布" --time-range week --need-content
  uv run search.py "新能源汽车政策" --industry gov --authoritative-only
  uv run search.py "故宫雪景" --type image --orientation landscape
  uv run search.py "latest AI research" --global --max-snippet-length 1000
  uv run search.py "同款连衣裙" --type visual --image-file ./dress.jpg --global

API key 解析顺序：--api-key > VOLC_WEB_SEARCH_API_KEY > WEB_SEARCH_API_KEY
  > ASK_ECHO_SEARCH_INFINITY_API_KEY > skill 目录 .env > 当前目录 .env
  获取地址：https://console.volcengine.com/search-infinity/api-key
        """,
    )

    parser.add_argument(
        "query",
        nargs="?",
        type=str,
        help="搜索关键词（1–100 字符，过长截断）；图搜图（--type visual）可省略。",
    )
    parser.add_argument(
        "--edition",
        choices=["custom", "global"],
        default="custom",
        help="搜索版本：custom（默认，低时延/过滤丰富/支持套餐 Key）或 global（全球站点/摘要可控/图搜图，仅按量后付费 Key）。",
    )
    parser.add_argument(
        "--global",
        dest="global_flag",
        action="store_true",
        help="等价于 --edition global。",
    )
    parser.add_argument(
        "--type",
        "-t",
        dest="search_type",
        choices=["web", "image", "visual"],
        default="web",
        help="搜索类型：web 文搜文（默认）、image 文搜图、visual 图搜图（仅 Global 版）。",
    )
    parser.add_argument(
        "--count",
        "-c",
        type=int,
        default=DEFAULT_COUNT,
        help=f"返回条数。Custom：web ≤ {CUSTOM_MAX_WEB_COUNT}、image ≤ {CUSTOM_MAX_IMAGE_COUNT}；Global ≤ {GLOBAL_MAX_COUNT}。",
    )

    # 结果控制（两个版本通用）
    parser.add_argument(
        "--orientation",
        choices=["landscape", "portrait", "square"],
        default=None,
        help="图片方向筛选（仅 --type image）：landscape 横图 / portrait 竖图 / square 方图。",
    )
    parser.add_argument(
        "--min-short-edge",
        type=int,
        default=0,
        help="图片短边最小像素（仅 --type image），适合找壁纸/高清图。",
    )
    parser.add_argument(
        "--queue",
        action="store_true",
        help="开启队列模式：超出 QPS 的请求排队等待（最多 10s）而非直接报 700429，适合批量调用。",
    )
    parser.add_argument(
        "--query-rewrite",
        action="store_true",
        help="（Custom）服务端 Query 改写，口语化长问题召回不好时使用（略增耗时）。",
    )

    # Custom 版专属
    parser.add_argument(
        "--time-range",
        type=str,
        default=None,
        help="（Custom）时间过滤：day/week/month/year、OneDay/OneWeek/OneMonth/OneYear 或 YYYY-MM-DD..YYYY-MM-DD。",
    )
    parser.add_argument(
        "--sites",
        type=str,
        default=None,
        help="（Custom）限定站点域名，多个用 | 分隔，最多 20 个，如 github.com|zhihu.com。",
    )
    parser.add_argument(
        "--block-sites",
        type=str,
        default=None,
        help="（Custom）屏蔽站点域名，多个用 | 分隔，最多 5 个。",
    )
    parser.add_argument(
        "--authoritative-only",
        action="store_true",
        help="（Custom）仅返回「非常权威」来源（政府/央媒/985-211 等）；结果会减少。",
    )
    parser.add_argument(
        "--industry",
        choices=["finance", "game", "health", "gov"],
        default=None,
        help="（Custom）行业垂类搜索：finance 金融 / game 游戏 / health 健康医疗 / gov 政府权威。",
    )
    parser.add_argument(
        "--need-content",
        action="store_true",
        help="（Custom web）仅保留有正文的结果（Content/Summary 默认即返回，无需此参数）。",
    )
    parser.add_argument(
        "--content-format",
        choices=["text", "markdown"],
        default=None,
        help="（Custom web）正文格式：text（默认）或 markdown。",
    )

    # Global 版专属
    parser.add_argument(
        "--icp-host-only",
        action="store_true",
        help="（Global）仅在国内 ICP 备案网站范围内搜索。",
    )
    parser.add_argument(
        "--max-snippet-length",
        type=int,
        default=0,
        help=f"（Global）单条摘要最大 tokens，≤ {MAX_SNIPPET_LENGTH_CAP}，推荐 1000 以内。",
    )
    parser.add_argument(
        "--max-images-per-doc",
        type=int,
        default=0,
        help=f"（Global）每条结果最多返回图片数，≤ {MAX_IMAGES_PER_DOC_CAP}，默认 3。",
    )
    parser.add_argument(
        "--image-url",
        type=str,
        default=None,
        help="（Global visual）图搜图的查询图片 URL（http/https，与 --image-file 二选一）。",
    )
    parser.add_argument(
        "--image-file",
        type=str,
        default=None,
        help="（Global visual）图搜图的本地图片路径，自动转 base64（与 --image-url 二选一）。",
    )
    parser.add_argument(
        "--roi",
        type=str,
        default=None,
        help="（Global visual）图搜图的感兴趣区域，格式 XMin,YMin,XMax,YMax（相对坐标 0~1，XMax>XMin、YMax>YMin）；只用图片子区域检索，如截图里只搜某个商品。",
    )

    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="输出结构化 JSON（包含完整 API 响应），供程序/Agent 消费。",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="显式传入 API Key（否则从环境变量 / .env 读取）。",
    )
    return parser


def validate_args(args: argparse.Namespace):
    if args.global_flag:
        args.edition = "global"

    # 图搜图为 Global 独占
    if args.search_type == "visual" and args.edition != "global":
        sys.exit("Error: 图搜图（--type visual）仅支持 Global 版，请加 --global。")

    # Query 校验：web/image 必填；visual 可空
    if args.search_type != "visual":
        if not args.query or not args.query.strip():
            sys.exit("Error: 请输入搜索词。")
        args.query = args.query.strip()
        if len(args.query) > 100:
            print(f"Warning: Query 超过 100 字符将被 API 截断（当前 {len(args.query)} 字符）。", file=sys.stderr)
            args.query = args.query[:100]

    if args.search_type == "visual":
        if not (args.image_url or args.image_file):
            sys.exit("Error: 图搜图需要 --image-url 或 --image-file 指定查询图片。")
    elif args.image_url or args.image_file:
        sys.exit("Error: --image-url/--image-file 仅在 --type visual（图搜图）时使用。")
    if args.image_url and args.image_file:
        sys.exit("Error: --image-url 与 --image-file 只能二选一。")

    # 图搜图子区域 --roi
    if args.roi is not None:
        if args.search_type != "visual":
            sys.exit("Error: --roi 仅用于 --type visual（图搜图）。")
        try:
            coords = [float(x) for x in args.roi.split(",")]
        except ValueError:
            sys.exit("Error: --roi 格式应为 XMin,YMin,XMax,YMax，如 0.1,0.2,0.7,0.9。")
        if len(coords) != 4 or not all(0.0 <= c <= 1.0 for c in coords):
            sys.exit("Error: --roi 需要 4 个 0~1 之间的相对坐标：XMin,YMin,XMax,YMax。")
        xmin, ymin, xmax, ymax = coords
        if xmax <= xmin or ymax <= ymin:
            sys.exit("Error: --roi 需满足 XMax>XMin、YMax>YMin。")
        args.roi = coords

    # 版本专属参数互斥检查
    if args.edition == "global":
        used = [flag for attr, flag, _ in CUSTOM_ONLY_FLAGS if getattr(args, attr)]
        if used:
            sys.exit(
                f"Error: {'、'.join(used)} 是 Custom 版专用请求参数，不能与 --global 同用。"
                "Global 版域名限定可写在 query 里（如 site:github.com 关键词）；"
                "时间/权威度/行业等可靠过滤请去掉 --global 使用 Custom 版。"
            )
    else:
        used = [flag for attr, flag, _ in GLOBAL_ONLY_FLAGS if getattr(args, attr)]
        if used:
            sys.exit(f"Error: {'、'.join(used)} 仅 Global 版支持，请加 --global。")

    # 文搜图（image）不支持的 web 专属参数，避免静默忽略
    if args.search_type == "image":
        web_only = []
        if args.time_range:
            web_only.append("--time-range")
        if args.industry:
            web_only.append("--industry")
        if args.content_format:
            web_only.append("--content-format")
        if args.need_content:
            web_only.append("--need-content")
        if web_only:
            sys.exit(f"Error: {'、'.join(web_only)} 仅文搜文（--type web）支持，文搜图不适用。")

    # 图片筛选参数只对文搜图（image）生效；图搜图 visual 不支持 ImageFilter
    if args.search_type != "image" and (args.orientation or args.min_short_edge):
        sys.exit("Error: --orientation / --min-short-edge 仅在 --type image（文搜图）时有效。")

    # Count 上限
    if args.count < 1:
        sys.exit("Error: --count 需 ≥ 1。")
    if args.edition == "custom":
        cap = CUSTOM_MAX_IMAGE_COUNT if args.search_type == "image" else CUSTOM_MAX_WEB_COUNT
    else:
        cap = GLOBAL_MAX_COUNT
    if args.count > cap:
        print(f"Warning: --count 超过上限 {cap}，已自动调整。", file=sys.stderr)
        args.count = cap

    args.time_range = normalize_time_range(args.time_range)


# ── Main ──────────────────────────────────────────────────────────────


def main():
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args)

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        sys.exit(
            "Error: 未找到豆包搜索 API Key。请任选一种方式配置：\n"
            "  1. 设置环境变量 VOLC_WEB_SEARCH_API_KEY（或 WEB_SEARCH_API_KEY）\n"
            "  2. 命令行传入 --api-key <KEY>\n"
            "  3. 在 skill 目录或当前目录创建 .env，写入 VOLC_WEB_SEARCH_API_KEY=<KEY>\n"
            "获取地址：https://console.volcengine.com/search-infinity/api-key\n"
            "注意：订阅套餐 Key 与按量后付费 Key 相互隔离；Global 版（--global）仅支持按量后付费 Key。"
        )

    if args.edition == "custom":
        payload = build_custom_payload(args)
    else:
        payload = build_global_payload(args)

    start = time.monotonic()
    try:
        data = call_search(args.edition, api_key, payload)
    except requests.exceptions.Timeout:
        sys.exit("Error: 请求超时（60s）。可稍后重试，或加 --queue 使用队列模式。")
    except requests.exceptions.ConnectionError:
        sys.exit("Error: 无法连接搜索服务，请检查网络连接。")
    elapsed = time.monotonic() - start

    if args.json_output:
        print(format_json(data, elapsed, args.edition, args.search_type))
    else:
        # Global 人类可读格式需要原始 query（响应里不回传）
        data["_query"] = args.query or ""
        if args.edition == "custom":
            print(format_custom_human(data, args.search_type, elapsed))
        else:
            print(format_global_human(data, args.search_type, elapsed))


if __name__ == "__main__":
    main()
