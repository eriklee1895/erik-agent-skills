"""Deterministic checks for self-contained Feishu html5-block documents."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

REQUIRED_META = {
    "viewport": "width=device-width, initial-scale=1",
    "use-iframe": "true",
}
HEIGHT_MODES = {"auto", "viewport"}
MAX_BYTES = 500 * 1024


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


class _DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.resources: list[tuple[str, str]] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta":
            if values.get("charset"):
                self.meta["charset"] = values["charset"] or ""
            name = values.get("name")
            if name:
                self.meta[name.lower()] = values.get("content", "") or ""
        for attribute in ("src", "href"):
            value = values.get(attribute)
            if value:
                self.resources.append((tag, value))

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def _finding(level: str, code: str, message: str) -> Finding:
    return Finding(level=level, code=code, message=message)


def validate_html(path: Path) -> ValidationResult:
    findings: list[Finding] = []
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return ValidationResult((_finding("error", "file-not-found", f"HTML file not found: {path}"),))

    if len(raw) > MAX_BYTES:
        findings.append(_finding("error", "file-too-large", f"HTML file exceeds {MAX_BYTES} bytes"))

    parser = _DocumentParser()
    source = raw.decode("utf-8", errors="replace")
    parser.feed(source)

    if "charset" not in parser.meta:
        findings.append(_finding("error", "missing-charset", "Document must declare a charset"))
    for name, expected in REQUIRED_META.items():
        if parser.meta.get(name) != expected:
            findings.append(_finding("error", "missing-meta", f'Meta {name!r} must be {expected!r}'))
    height_mode = parser.meta.get("html-box-height-mode")
    if height_mode is not None and height_mode not in HEIGHT_MODES:
        findings.append(_finding("error", "invalid-height-mode", f"Unknown height mode: {height_mode}"))
    if not parser.meta.get("description", "").strip():
        findings.append(_finding("error", "missing-description", "Document must declare a description"))

    if any(value.lower().startswith(("http://", "https://", "//")) for _, value in parser.resources):
        findings.append(_finding("warning", "external-resource", "Document references an external resource"))
    if re.search(r"data:[^\s\"']+;base64,", source, re.IGNORECASE):
        findings.append(_finding("warning", "inline-base64", "Document contains inline base64 data"))
    if re.search(r"(?:api[_-]?key|secret|token|password)\s*[:=]\s*[^\s<]+", source, re.IGNORECASE):
        findings.append(_finding("warning", "secret-like-content", "Document contains secret-like content"))
    has_animation = re.search(r"\banimation(?:-name)?\s*:|@keyframes\b", source, re.IGNORECASE)
    has_reduced_motion = re.search(r"prefers-reduced-motion", source, re.IGNORECASE)
    if has_animation and not has_reduced_motion:
        findings.append(_finding("warning", "missing-reduced-motion", "Animation lacks reduced-motion handling"))

    return ValidationResult(tuple(findings))


def main(argv: list[str] | None = None) -> int:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("path", type=Path)
    args = argument_parser.parse_args(argv)
    result = validate_html(args.path)
    for finding in result.findings:
        print(f"{finding.level}: {finding.code}: {finding.message}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
