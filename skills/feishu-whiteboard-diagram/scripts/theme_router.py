#!/usr/bin/env python3
"""Suggest a palette; preserve explicit identity and the agent's chosen design."""

from __future__ import annotations

import argparse


PURPOSE_THEMES = {
    "architecture": "light-technical",
    "process": "light-technical",
    "state": "light-technical",
    "swimlane": "light-technical",
    "benchmark": "white-report",
    "comparison": "riptide-cobalt",
    "quadrant": "grove",
    "focus-detail": "avocado-press",
}

TONE_THEMES = {
    "creative": "riso-brut",
    "governance": "grove",
    "benchmark": "white-report",
}


def resolve_theme(
    *,
    user_theme: str | None = None,
    brand_theme: str | None = None,
    existing_theme: str | None = None,
    selected_theme: str | None = None,
    diagram_purpose: str | None = None,
    article_tone: str | None = None,
) -> str:
    """Return an advisory suggestion, not an allowlist or visual-quality verdict."""

    for explicit in (user_theme, brand_theme, existing_theme, selected_theme):
        if explicit and explicit.strip():
            return explicit.strip().lower()

    purpose = (diagram_purpose or "").strip().lower()
    tone = (article_tone or "").strip().lower()
    if purpose == "comparison" and tone == "benchmark":
        return "white-report"
    if purpose == "timeline":
        return "coral" if tone in {"creative", "product"} else "light-technical"
    if tone in {"creative", "governance"}:
        return TONE_THEMES[tone]
    if purpose in PURPOSE_THEMES:
        return PURPOSE_THEMES[purpose]

    return TONE_THEMES.get(tone, "light-technical")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-theme")
    parser.add_argument("--brand-theme")
    parser.add_argument("--existing-theme")
    parser.add_argument(
        "--theme",
        dest="selected_theme",
        help="Agent-selected preset, adaptation or custom palette",
    )
    parser.add_argument("--purpose", dest="diagram_purpose")
    parser.add_argument("--tone", dest="article_tone")
    args = parser.parse_args()
    print(
        resolve_theme(
            user_theme=args.user_theme,
            brand_theme=args.brand_theme,
            existing_theme=args.existing_theme,
            selected_theme=args.selected_theme,
            diagram_purpose=args.diagram_purpose,
            article_tone=args.article_tone,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
