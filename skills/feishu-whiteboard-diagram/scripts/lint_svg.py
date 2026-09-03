#!/usr/bin/env python3
"""Preflight checks for Feishu whiteboard SVG (editable-node medium)."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


UNSUPPORTED_TAGS = {"clippath", "mask", "pattern", "foreignobject"}
FLATTEN_TAGS = {"polygon", "path"}
OPACITY_ATTRS = {"opacity", "fill-opacity", "stroke-opacity"}
ARROW_TAGS = {"line", "polyline"}


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    findings: tuple[Finding, ...]

    @property
    def ok(self) -> bool:
        return not any(finding.level == "error" for finding in self.findings)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _finding(level: str, code: str, message: str) -> Finding:
    return Finding(level, code, message)


def validate_svg(path: Path) -> ValidationResult:
    findings: list[Finding] = []
    if not path.exists():
        return ValidationResult((_finding("error", "file-not-found", f"Missing {path}"),))

    raw = path.read_bytes()
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError:
        return ValidationResult(
            (_finding("error", "invalid-utf8", "SVG must be saved as UTF-8"),)
        )

    if not source.strip():
        return ValidationResult((_finding("error", "empty-file", "SVG file is empty"),))

    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        return ValidationResult(
            (_finding("error", "invalid-xml", f"Cannot parse SVG: {exc}"),)
        )

    if _local_name(root.tag) != "svg":
        findings.append(
            _finding("error", "missing-svg-root", "Root element must be <svg>")
        )

    view_box = root.attrib.get("viewBox") or root.attrib.get("viewbox")
    if not view_box:
        findings.append(
            _finding("error", "missing-viewbox", "Add a viewBox on the root <svg>")
        )

    has_marker = False
    has_text = False
    has_arrow_line = False
    has_marker_end = False

    for el in root.iter():
        tag = _local_name(el.tag)
        if tag in UNSUPPORTED_TAGS:
            findings.append(
                _finding(
                    "error",
                    "unsupported-tag",
                    f"<{tag}> is not supported by the whiteboard SVG parser",
                )
            )
        if tag == "marker":
            has_marker = True
        if tag in {"text", "tspan"} and (el.text or "").strip():
            has_text = True
        if tag in ARROW_TAGS:
            has_arrow_line = True
            ends = el.attrib.get("marker-end") or el.attrib.get("marker-start")
            if ends:
                has_marker_end = True
        if "font-family" in el.attrib or "font-family" in (el.attrib.get("style") or ""):
            findings.append(
                _finding(
                    "error",
                    "font-family",
                    "Do not set font-family; the board hardcodes Noto Sans SC",
                )
            )
        style = el.attrib.get("style") or ""
        for attr in OPACITY_ATTRS:
            if attr in el.attrib or re.search(rf"{attr}\s*:", style):
                findings.append(
                    _finding(
                        "warning",
                        "opacity",
                        "Opacity is unreliable on the live board; use a solid lighter hex",
                    )
                )
                break
        href = el.attrib.get("href") or el.attrib.get("{http://www.w3.org/1999/xlink}href")
        if href and not str(href).startswith("#"):
            findings.append(
                _finding(
                    "error",
                    "external-resource",
                    "SVG must be self-contained; do not reference external href",
                )
            )

    parent_map = {c: p for p in root.iter() for c in p}
    for el in root.iter():
        tag = _local_name(el.tag)
        if tag not in FLATTEN_TAGS:
            continue
        node = el
        in_defs = False
        while node is not None and node is not root:
            parent = parent_map.get(node)
            if parent is not None and _local_name(parent.tag) in {"defs", "marker"}:
                in_defs = True
                break
            node = parent
        if in_defs:
            continue
        findings.append(
            _finding(
                "warning",
                "flatten-to-svg-node",
                f"<{tag}> becomes an embedded SVG node, not a native shape; OK for one diamond, not for structure",
            )
        )

    if not has_text:
        findings.append(
            _finding("error", "missing-text", "Diagram has no <text> labels")
        )
    if has_arrow_line and not has_marker_end:
        findings.append(
            _finding(
                "warning",
                "missing-marker-end",
                "Lines/polylines should use marker-end so the board creates native arrowheads",
            )
        )
    if has_arrow_line and not has_marker:
        findings.append(
            _finding(
                "warning",
                "missing-marker-def",
                "Define a <marker id=\"arrow\"> in <defs> and reference it from connectors",
            )
        )
    if re.search(r"(?:api[_-]?key|secret|token|password)\s*[:=]\s*\S+", source, re.I):
        findings.append(
            _finding("warning", "secret-like-content", "Review possible sensitive content")
        )

    # de-duplicate identical findings
    unique: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for finding in findings:
        key = (finding.level, finding.code)
        if finding.code in {"flatten-to-svg-node", "opacity", "font-family", "unsupported-tag"}:
            if key in seen:
                continue
            seen.add(key)
        unique.append(finding)

    return ValidationResult(tuple(unique))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    result = validate_svg(args.path)
    for finding in result.findings:
        print(f"{finding.level}: {finding.code}: {finding.message}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
