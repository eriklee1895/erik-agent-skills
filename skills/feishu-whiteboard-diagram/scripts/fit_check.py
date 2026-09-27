#!/usr/bin/env python3
"""Deterministic pre-render fit checks for editable Feishu SVG boards.

This checker deliberately stays narrower than visual review. It catches canvas
bleed, weak outer margins, and large dead bands before the whiteboard CLI is
run. Text width is an estimate because the board owns the font and reflows CJK
by character; the rendered PNG remains the authority for final typography.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path


NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    message: str


@dataclass(frozen=True)
class FitResult:
    findings: tuple[Finding, ...]
    bbox: tuple[float, float, float, float] | None = None
    view_box: tuple[float, float, float, float] | None = None

    @property
    def ok(self) -> bool:
        return not any(finding.level == "error" for finding in self.findings)

    @property
    def errors(self) -> tuple[Finding, ...]:
        return tuple(finding for finding in self.findings if finding.level == "error")

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return tuple(
            finding for finding in self.findings if finding.level == "warning"
        )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _number(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    match = NUMBER_RE.search(value)
    return float(match.group(0)) if match else default


def _numbers(value: str | None) -> list[float]:
    return [float(match.group(0)) for match in NUMBER_RE.finditer(value or "")]


def _view_box(root: ET.Element) -> tuple[float, float, float, float] | None:
    values = _numbers(root.attrib.get("viewBox") or root.attrib.get("viewbox"))
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        return None
    return tuple(values)  # type: ignore[return-value]


def _merge(
    current: tuple[float, float, float, float] | None,
    candidate: tuple[float, float, float, float] | None,
) -> tuple[float, float, float, float] | None:
    if candidate is None:
        return current
    if current is None:
        return candidate
    return (
        min(current[0], candidate[0]),
        min(current[1], candidate[1]),
        max(current[2], candidate[2]),
        max(current[3], candidate[3]),
    )


def _text_width(text: str, font_size: float) -> float:
    width_units = 0.0
    for character in text:
        if character.isspace():
            width_units += 0.35
        elif ord(character) >= 0x2E80:
            width_units += 1.0
        else:
            width_units += 0.6
    return width_units * font_size


def _element_bbox(
    element: ET.Element,
    view_box: tuple[float, float, float, float],
) -> tuple[float, float, float, float] | None:
    tag = _local_name(element.tag)
    x0, y0, width, height = view_box
    if tag == "rect":
        x = _number(element.attrib.get("x"))
        y = _number(element.attrib.get("y"))
        w = _number(element.attrib.get("width"))
        h = _number(element.attrib.get("height"))
        if x == x0 and y == y0 and w == width and h == height:
            return None
        return (x, y, x + w, y + h) if w >= 0 and h >= 0 else None
    if tag == "circle":
        cx = _number(element.attrib.get("cx"))
        cy = _number(element.attrib.get("cy"))
        radius = _number(element.attrib.get("r"))
        return (cx - radius, cy - radius, cx + radius, cy + radius)
    if tag == "ellipse":
        cx = _number(element.attrib.get("cx"))
        cy = _number(element.attrib.get("cy"))
        rx = _number(element.attrib.get("rx"))
        ry = _number(element.attrib.get("ry"))
        return (cx - rx, cy - ry, cx + rx, cy + ry)
    if tag == "line":
        x1 = _number(element.attrib.get("x1"))
        y1 = _number(element.attrib.get("y1"))
        x2 = _number(element.attrib.get("x2"))
        y2 = _number(element.attrib.get("y2"))
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    if tag == "polyline":
        values = _numbers(element.attrib.get("points"))
        if len(values) < 2:
            return None
        xs = values[0::2]
        ys = values[1::2]
        return (min(xs), min(ys), max(xs), max(ys))
    if tag == "text" and (element.text or "").strip():
        font_size = _number(element.attrib.get("font-size"), 16)
        text = " ".join((element.text or "").split())
        text_width = _text_width(text, font_size)
        x = _number(element.attrib.get("x"))
        y = _number(element.attrib.get("y"))
        anchor = element.attrib.get("text-anchor", "start")
        if anchor == "middle":
            x -= text_width / 2
        elif anchor == "end":
            x -= text_width
        return (x, y - font_size, x + text_width, y + font_size * 0.25)
    return None


def check_svg_fit(
    path: Path,
    *,
    margin: float = 80,
    deadband: float = 80,
) -> FitResult:
    findings: list[Finding] = []
    if not path.exists():
        return FitResult((Finding("error", "file-not-found", f"Missing {path}"),))

    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return FitResult((Finding("error", "invalid-utf8", "SVG must be UTF-8"),))
    except ET.ParseError as exc:
        return FitResult((Finding("error", "invalid-xml", str(exc)),))

    view_box = _view_box(root)
    if view_box is None:
        return FitResult(
            (Finding("error", "missing-viewbox", "Add a positive four-value viewBox"),)
        )

    parent_map = {child: parent for parent in root.iter() for child in parent}
    bbox: tuple[float, float, float, float] | None = None
    for element in root.iter():
        node = element
        inside_defs = False
        while node is not root:
            node = parent_map.get(node, root)
            if _local_name(node.tag) in {"defs", "marker"}:
                inside_defs = True
                break
        if inside_defs or _local_name(element.tag) in {"svg", "defs", "marker", "tspan"}:
            continue
        bbox = _merge(bbox, _element_bbox(element, view_box))

    if bbox is None:
        findings.append(
            Finding("warning", "empty-content", "No measurable native content found")
        )
        return FitResult(tuple(findings), bbox, view_box)

    vx, vy, vw, vh = view_box
    right = vx + vw
    bottom = vy + vh
    min_x, min_y, max_x, max_y = bbox
    if min_x < vx or min_y < vy or max_x > right or max_y > bottom:
        findings.append(
            Finding(
                "error",
                "canvas-bleed",
                f"Content bbox {bbox} exceeds viewBox {view_box}",
            )
        )

    margins = {
        "left": min_x - vx,
        "top": min_y - vy,
        "right": right - max_x,
        "bottom": bottom - max_y,
    }
    for side, available in margins.items():
        if 0 <= available < margin:
            findings.append(
                Finding(
                    "warning",
                    f"outer-margin-{side}",
                    f"Outer {side} margin is {available:.0f}px; target is {margin:.0f}px",
                )
            )

    for side, available in (
        ("right", margins["right"] - margin),
        ("bottom", margins["bottom"] - margin),
    ):
        if available > deadband:
            findings.append(
                Finding(
                    "warning",
                    f"deadspace-{side}",
                    f"Dead {side} band is about {available:.0f}px after the outer margin",
                )
            )

    return FitResult(tuple(findings), bbox, view_box)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path)
    parser.add_argument("--margin", type=float, default=80)
    parser.add_argument("--deadband", type=float, default=80)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = check_svg_fit(args.svg, margin=args.margin, deadband=args.deadband)
    if args.json:
        payload = {
            "file": str(args.svg),
            "ok": result.ok,
            "bbox": result.bbox,
            "viewBox": result.view_box,
            "findings": [asdict(finding) for finding in result.findings],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"fit-check {args.svg}")
        print("  ✓ no predicted fit defects" if result.ok else "  ✗ predicted fit defects")
        for finding in result.findings:
            print(f"  {'ERROR' if finding.level == 'error' else 'WARN'} {finding.code}: {finding.message}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
