#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "volcenginesdkcore>=1.0",
#   "volcenginesdkspeechsaasprod>=1.0",
#   "python-dotenv>=1.0",
# ]
# ///
"""refresh-speakers.py — 从 ListSpeakers API 拉全量音色并更新 speakers.json + speakers.md。

低频手动运行，需 VOLC_ACCESSKEY / VOLC_SECRETKEY（AK/SK 鉴权，非合成接口的 VOLC_SPEECH_API_KEY）。
volcenginesdkcore / volcenginesdkspeechsaasprod 为内部 SDK 包，需预先从内部 registry 安装。

用法:
    uv run scripts/refresh-speakers.py

The ListSpeakers snapshot is the same official catalog that seed-audio-gen
uses. Keep the two speakers.json files in sync when refreshing; only the
curated speakers.md scene order differs (TTS leads with 教学/客服).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Per-scene cap in the curated speakers.md quick reference. The full catalog
# lives in speakers.json and is queried via `--list-speakers`; the md file is a
# short-listing aid, not a complete dump.
TOP_VOICES_PER_SCENE = 5

# volcengine-tts is a narration / service-voice skill, so teaching and
# customer-service voices come before character-acting scenes — unlike
# seed-audio-gen, which leads with 角色扮演. 其他 (uncategorized) sorts last.
_SCENE_ORDER = [
    "通用场景",   # default narration (Vivi 2.0 lives here)
    "教学场景",   # education / explainer — high priority for this skill
    "客服场景",   # customer-service / brand read
    "视频配音",   # film / ad dubbing
    "有声阅读",   # audiobook narration
    "多语种",     # non-Chinese
    "趣味口音",   # accented / character voices
    "角色扮演",   # multi-character / drama (large, browse via --filter)
]


def _scene_sort_key(scene: str) -> tuple[int, str]:
    """Narration-first scene ordering for TTS; unknown scenes sorted
    after the known ones, with 其他 pinned last."""
    if scene in _SCENE_ORDER:
        return (_SCENE_ORDER.index(scene), scene)
    if scene == "其他":
        return (999, scene)
    return (900, scene)


def build_speakers_md(
    speakers: list[dict[str, Any]],
    *,
    as_of: str | None = None,
) -> str:
    """Build a CURATED speakers.md quick reference: Top-N voices per scene.

    This is intentionally not a full dump of speakers.json — it is a short,
    low-context shortlist with trial links. The full catalog is queried via
    `--list-speakers`; agents should not read speakers.json into context
    (it is ~220KB). `as_of` is the catalog snapshot date; defaults to today
    (used when refreshing from ListSpeakers)."""
    bigtts_count = sum(1 for s in speakers if s["type"] == "bigtts")
    icl_count = sum(1 for s in speakers if s["type"] == "icl")
    total = len(speakers)
    today = as_of or date.today().isoformat()

    lines: list[str] = [
        "# seed-tts-2.0 音色速查（精选）",
        "",
        f"> 本表为**精选速查**：每场景按热度列 Top {TOP_VOICES_PER_SCENE}，带试听链接。"
        f"全量 {total} 个音色（{bigtts_count} bigtts + {icl_count} ICL，截至 {today}）在 `speakers.json`，"
        f"请勿把 speakers.json 读进上下文（约 220KB）；用下列命令查询。"
        f"与 seed-audio-gen 共用同一份 ListSpeakers 快照；ICL/`_tob` 音色合成时通常要加 `--model seed-tts-2.0-standard`。",
        "",
        "```bash",
        "uv run scripts/volcengine-tts.py --list-speakers                          # 全量",
        "uv run scripts/volcengine-tts.py --list-speakers --filter type=bigtts     # 官方 2.0 公有音色",
        "uv run scripts/volcengine-tts.py --list-speakers --filter scene=教学场景   # 按场景",
        "uv run scripts/volcengine-tts.py --list-speakers --filter lang=ja --sort heat",
        "```",
        "",
        "需要某个场景的全量音色时，跑 `--list-speakers --filter scene=<场景>`。日常旁白优先 `type=bigtts`。",
        "",
    ]

    # Group by scene
    by_scene: dict[str, list[dict[str, Any]]] = {}
    for s in speakers:
        scene = s.get("scene", "其他")
        by_scene.setdefault(scene, []).append(s)

    for scene in sorted(by_scene.keys(), key=_scene_sort_key):
        items = sorted(by_scene[scene], key=lambda s: -s.get("heat", 0))
        shown = items[:TOP_VOICES_PER_SCENE]
        lines.append(
            f"## {scene}（本场景共 {len(items)} 个，列 Top {len(shown)}；全量用 "
            f"`--list-speakers --filter scene={scene}`）"
        )
        lines.append("")
        lines.append("| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |")
        lines.append("|---|---|---|---|---|---|")
        for item in shown:
            emoji = item.get("emoji", "")
            name = f"{emoji} {item['name']}" if emoji else item["name"]
            vt = f"`{item['voice_type']}`"
            gender = item.get("gender", "")
            desc = item.get("description", "")
            trial = item.get("trial_url", "")
            trial_link = f"[试听]({trial})" if trial else ""
            heat = item.get("heat", 0)
            lines.append(f"| {name} | {vt} | {gender} | {desc} | {trial_link} | {heat} |")
        lines.append("")

    return "\n".join(lines)

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REFERENCES_DIR = SKILL_DIR / "references"
SPEAKERS_JSON = REFERENCES_DIR / "speakers.json"
SPEAKERS_MD = REFERENCES_DIR / "speakers.md"


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_credentials() -> tuple[str, str]:
    """三級 fallback: env → .env → ~/.volcengine.env"""
    ak = os.environ.get("VOLC_ACCESSKEY", "").strip()
    sk = os.environ.get("VOLC_SECRETKEY", "").strip()
    if ak and sk:
        return ak, sk

    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env)
        ak = os.environ.get("VOLC_ACCESSKEY", "").strip()
        sk = os.environ.get("VOLC_SECRETKEY", "").strip()
        if ak and sk:
            return ak, sk

    user_env = Path.home() / ".volcengine.env"
    if user_env.exists():
        load_dotenv(user_env)
        ak = os.environ.get("VOLC_ACCESSKEY", "").strip()
        sk = os.environ.get("VOLC_SECRETKEY", "").strip()
        if ak and sk:
            return ak, sk

    die(
        "VOLC_ACCESSKEY / VOLC_SECRETKEY not found. "
        "Set via env, .env, or ~/.volcengine.env"
    )


def fetch_all_speakers(ak: str, sk: str) -> list[dict[str, Any]]:
    """分页调 ListSpeakers API 拉全量音色列表。"""
    from volcenginesdkcore import Configuration
    from volcenginesdkspeechsaasprod import (
        SPEECHSAASPRODApi,
        ListSpeakersRequest,
    )

    Configuration.set_default(
        Configuration(ak=ak, sk=sk, region="cn-beijing")
    )
    api = SPEECHSAASPRODApi()

    all_speakers: list[dict[str, Any]] = []
    page = 1
    while True:
        try:
            resp = api.list_speakers(ListSpeakersRequest(page=page))
        except Exception as e:
            die(f"ListSpeakers API call failed on page {page}: {e}")

        result = resp.get("Result") if isinstance(resp, dict) else {}
        if not result:
            # Try attribute access (SDK may return object)
            result = getattr(resp, "Result", None) if hasattr(resp, "Result") else None
            if result is None:
                die(f"Unexpected response shape on page {page}: {type(resp)}")

        if isinstance(result, dict):
            speakers = result.get("Speakers", [])
            total = result.get("Total", 0)
        else:
            speakers = getattr(result, "Speakers", [])
            total = getattr(result, "Total", 0)

        if not speakers:
            break

        # Normalize each speaker to dict
        for s in speakers:
            if isinstance(s, dict):
                all_speakers.append(s)
            else:
                all_speakers.append(_obj_to_dict(s))

        print(f"  Page {page}: fetched {len(speakers)} speakers (total {total}, accumulated {len(all_speakers)})")
        if len(all_speakers) >= total:
            break
        page += 1

    return all_speakers


def _obj_to_dict(obj: Any) -> dict[str, Any]:
    """Convert SDK object to plain dict."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    result: dict[str, Any] = {}
    for key in dir(obj):
        if key.startswith("_"):
            continue
        val = getattr(obj, key)
        if callable(val):
            continue
        result[key] = _obj_to_dict(val) if not isinstance(val, (str, int, float, bool, list, dict, type(None))) else val
    return result


def _first_category(speaker: dict[str, Any]) -> str:
    """Extract first scene category from raw speaker entry."""
    categories = speaker.get("Categories", [])
    if isinstance(categories, list) and categories:
        first = categories[0]
        if isinstance(first, dict):
            sub = first.get("Categories", [])
            if isinstance(sub, list) and sub:
                return str(sub[0])
    return "其他"


def _language_codes(speaker: dict[str, Any]) -> list[str]:
    """Extract language codes from raw speaker Languages list."""
    langs = speaker.get("Languages", [])
    if not isinstance(langs, list):
        return []
    codes: list[str] = []
    for lang in langs:
        if isinstance(lang, dict):
            code = lang.get("Language", "")
            if code:
                codes.append(code)
    return codes


def _voice_type(speaker: dict[str, Any]) -> str:
    """Determine voice type: 'icl' for ICL/tob voices, 'bigtts' otherwise."""
    vt = speaker.get("VoiceType", "")
    if "ICL_" in vt or "_tob" in vt:
        return "icl"
    return "bigtts"


def process_speakers(raw_speakers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert raw ListSpeakers entries to speakers.json structure."""
    processed: list[dict[str, Any]] = []
    for s in raw_speakers:
        entry = {
            "voice_type": s.get("VoiceType", ""),
            "name": s.get("Name", ""),
            "type": _voice_type(s),
            "gender": s.get("Gender", ""),
            "age": s.get("Age", ""),
            "scene": _first_category(s),
            "description": s.get("Description", ""),
            "languages": _language_codes(s),
            "trial_url": s.get("TrialURL", "") or s.get("ShortTrialURL", ""),
            "heat": s.get("Heat", 0),
            "status": s.get("Status", "online"),
            "emoji": s.get("Emoji", ""),
        }
        processed.append(entry)
    return processed


def write_speakers_json(speakers: list[dict[str, Any]], path: Path) -> None:
    """Write speakers.json with 2-space indent, utf-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(speakers, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def rebuild_speakers_md_from_json(
    path: Path = SPEAKERS_JSON,
    *,
    as_of: str | None = None,
) -> str:
    """Rebuild speakers.md from an existing speakers.json snapshot (no API)."""
    speakers = json.loads(path.read_text(encoding="utf-8"))
    md_content = build_speakers_md(speakers, as_of=as_of)
    SPEAKERS_MD.write_text(md_content, encoding="utf-8")
    return md_content


def main() -> None:
    ak, sk = load_credentials()
    print("Fetching all speakers from ListSpeakers API...")
    raw = fetch_all_speakers(ak, sk)
    print(f"Total raw speakers: {len(raw)}")

    processed = process_speakers(raw)
    print(f"Processed: {len(processed)} speakers")

    write_speakers_json(processed, SPEAKERS_JSON)
    print(f"Wrote {SPEAKERS_JSON}")

    md_content = build_speakers_md(processed)
    SPEAKERS_MD.write_text(md_content, encoding="utf-8")
    print(f"Wrote {SPEAKERS_MD}")

    print(f"\nDone. {len(processed)} speakers written to speakers.json + speakers.md")


if __name__ == "__main__":
    main()
