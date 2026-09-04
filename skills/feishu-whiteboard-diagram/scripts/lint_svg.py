#!/usr/bin/env python3
"""Preflight checks for Feishu whiteboard SVG (editable-node medium)."""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


UNSUPPORTED_TAGS = {"clippath", "mask", "pattern", "foreignobject"}
FLATTEN_TAGS = {"polygon"}
OPACITY_ATTRS = {"opacity", "fill-opacity", "stroke-opacity"}
CONNECTOR_TAGS = {"line", "polyline", "path"}
DIRECTED_ROLES = {"connector", "directed-edge", "edge"}
UNDIRECTED_ROLES = {"axis", "divider", "guide", "spoke"}
MARKER_REF_RE = re.compile(r"^url\(#([^)]+)\)$")
HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


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


def _is_in_definitions(
    element: ET.Element,
    root: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> bool:
    node = element
    while node is not root:
        parent = parent_map.get(node)
        if parent is None:
            return False
        if _local_name(parent.tag) in {"defs", "marker"}:
            return True
        node = parent
    return False


def _element_label(element: ET.Element, index: int) -> str:
    identifier = element.attrib.get("id")
    suffix = f' id="{identifier}"' if identifier else f" #{index}"
    return f"<{_local_name(element.tag)}{suffix}>"


def _style_value(style: str, property_name: str) -> str | None:
    match = re.search(
        rf"(?:^|;)\s*{re.escape(property_name)}\s*:\s*([^;]+)",
        style,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _hex_rgb(value: str) -> tuple[float, float, float] | None:
    match = HEX_COLOR_RE.fullmatch(value.strip())
    if not match:
        return None
    raw = match.group(1)
    if len(raw) == 3:
        raw = "".join(character * 2 for character in raw)
    return tuple(int(raw[offset : offset + 2], 16) / 255 for offset in (0, 2, 4))


def _relative_luminance(value: str) -> float | None:
    rgb = _hex_rgb(value)
    if rgb is None:
        return None
    linear = tuple(
        channel / 12.92
        if channel <= 0.04045
        else math.pow((channel + 0.055) / 1.055, 2.4)
        for channel in rgb
    )
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float | None:
    """Return WCAG contrast for hex colors, or None for unsupported formats."""

    foreground_luminance = _relative_luminance(foreground)
    background_luminance = _relative_luminance(background)
    if foreground_luminance is None or background_luminance is None:
        return None
    lighter, darker = sorted((foreground_luminance, background_luminance), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _contrast_minimum(element: ET.Element) -> float:
    size_value = element.attrib.get("font-size", "0").removesuffix("px")
    try:
        font_size = float(size_value)
    except ValueError:
        font_size = 0

    weight_value = element.attrib.get("font-weight", "400").lower()
    try:
        font_weight = int(weight_value)
    except ValueError:
        font_weight = 700 if weight_value == "bold" else 400

    return 3.0 if font_size >= 24 or (font_size >= 19 and font_weight >= 700) else 4.5


def validate_svg(path: Path) -> ValidationResult:
    findings: list[Finding] = []
    if not path.exists():
        return ValidationResult(
            (_finding("error", "file-not-found", f"Missing {path}"),)
        )

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

    parent_map = {child: parent for parent in root.iter() for child in parent}
    marker_ids = {
        element.attrib["id"]
        for element in root.iter()
        if _local_name(element.tag) == "marker" and element.attrib.get("id")
    }
    has_text = False

    for index, element in enumerate(root.iter()):
        tag = _local_name(element.tag)
        label = _element_label(element, index)
        style = element.attrib.get("style") or ""

        if tag in UNSUPPORTED_TAGS:
            findings.append(
                _finding(
                    "error",
                    "unsupported-tag",
                    f"{label} is not supported by the whiteboard SVG parser",
                )
            )

        if tag in {"text", "tspan"} and (element.text or "").strip():
            has_text = True

        if "font-family" in element.attrib or _style_value(style, "font-family"):
            findings.append(
                _finding(
                    "error",
                    "font-family",
                    f"{label} sets font-family, but the board hardcodes Noto Sans SC",
                )
            )

        for attribute in OPACITY_ATTRS:
            if attribute in element.attrib or _style_value(style, attribute):
                findings.append(
                    _finding(
                        "warning",
                        "opacity",
                        f"{label} uses {attribute}; use a solid lighter hex for reliable live rendering",
                    )
                )
                break

        background = element.attrib.get("data-bg")
        if tag in {"text", "tspan"} and background:
            foreground = element.attrib.get("fill") or _style_value(style, "fill")
            ratio = contrast_ratio(foreground or "", background)
            if ratio is not None:
                minimum = _contrast_minimum(element)
                if ratio < minimum:
                    findings.append(
                        _finding(
                            "error",
                            "low-contrast",
                            f"{label} contrast {ratio:.2f}:1 is below {minimum:.1f}:1; change fill or data-bg",
                        )
                    )

        href = element.attrib.get("href") or element.attrib.get(
            "{http://www.w3.org/1999/xlink}href"
        )
        if href and not str(href).startswith("#"):
            findings.append(
                _finding(
                    "error",
                    "external-resource",
                    f"{label} references an external href; SVG must be self-contained",
                )
            )

    for index, element in enumerate(root.iter()):
        if _is_in_definitions(element, root, parent_map):
            continue

        tag = _local_name(element.tag)
        label = _element_label(element, index)
        style = element.attrib.get("style") or ""
        role = element.attrib.get("data-role", "").strip().lower()
        marker_attributes = {
            attribute: element.attrib.get(attribute) or _style_value(style, attribute)
            for attribute in ("marker-start", "marker-end")
            if element.attrib.get(attribute) or _style_value(style, attribute)
        }

        if tag in FLATTEN_TAGS:
            findings.append(
                _finding(
                    "warning",
                    "flatten-to-svg-node",
                    f"{label} becomes an embedded SVG node, not a native shape; OK for one diamond, not for structure",
                )
            )
        elif tag == "path" and not marker_attributes and role not in DIRECTED_ROLES:
            findings.append(
                _finding(
                    "warning",
                    "flatten-to-svg-node",
                    f"{label} has no connector role or marker; verify whether it stays editable",
                )
            )

        if tag not in CONNECTOR_TAGS:
            continue

        if role in DIRECTED_ROLES and not marker_attributes:
            findings.append(
                _finding(
                    "error",
                    "missing-marker-end",
                    f"{label} is a directed edge but has no marker-start or marker-end",
                )
            )

        for attribute, marker_value in marker_attributes.items():
            match = MARKER_REF_RE.fullmatch(str(marker_value).strip())
            marker_id = match.group(1) if match else None
            if marker_id is None or marker_id not in marker_ids:
                findings.append(
                    _finding(
                        "error",
                        "missing-marker-reference",
                        f"{label} {attribute} references an undefined marker: {marker_value}",
                    )
                )

        if role in UNDIRECTED_ROLES and marker_attributes:
            findings.append(
                _finding(
                    "warning",
                    "unexpected-marker",
                    f"{label} is role={role} but declares an arrow marker",
                )
            )

    if not has_text:
        findings.append(
            _finding("error", "missing-text", "Diagram has no <text> labels")
        )
    if re.search(r"(?:api[_-]?key|secret|token|password)\s*[:=]\s*\S+", source, re.I):
        findings.append(
            _finding(
                "warning", "secret-like-content", "Review possible sensitive content"
            )
        )

    unique: list[Finding] = []
    seen: set[tuple[str, str, str]] = set()
    for finding in findings:
        key = (finding.level, finding.code, finding.message)
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
