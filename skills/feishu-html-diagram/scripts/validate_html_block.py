"""Lightweight preflight checks for a Feishu html5-block file."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


MAX_BYTES = 500 * 1024
HEIGHT_MODES = {"auto", "viewport"}
RESOURCE_ATTRIBUTES = {"src", "href", "xlink:href", "poster"}


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


class _PreflightParser(HTMLParser):
    """Collect embed metadata without pretending to be an HTML5 validator."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doctype_html = False
        self.seen: set[str] = set()
        self.in_head = False
        self.in_title = False
        self.meta: dict[str, str] = {}
        self.title_text: list[str] = []
        self.resources: list[str] = []

    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower() == "doctype html":
            self.doctype_html = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {name.lower(): value or "" for name, value in attrs}
        if tag in {"html", "head", "body"}:
            self.seen.add(tag)
        if tag == "head":
            self.in_head = True
        if tag == "title" and self.in_head:
            self.in_title = True
        if tag == "meta" and self.in_head:
            if "charset" in values:
                self.meta["charset"] = values["charset"]
            name = values.get("name", "").lower()
            if name:
                self.meta[name] = values.get("content", "")
        self.resources.extend(
            value
            for name, value in attrs
            if value
            and (
                name.lower() in RESOURCE_ATTRIBUTES
                or (tag == "object" and name.lower() == "data")
            )
        )

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if tag == "head":
            self.in_head = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_text.append(data)


def _finding(level: str, code: str, message: str) -> Finding:
    return Finding(level=level, code=code, message=message)


def _resource_kind(value: str) -> str | None:
    normalized = value.strip().lower()
    if not normalized or normalized.startswith(("#", "data:", "blob:")):
        return None
    if normalized.startswith(("http://", "https://", "//")):
        return "external"
    if re.match(r"^[a-z][a-z0-9+.-]*:", normalized):
        return None
    return "relative"


def _resource_values(source: str) -> list[str]:
    resources = [
        match.group(2).strip()
        for match in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)", source, re.I)
    ]
    resources.extend(
        match.group(1)
        for match in re.finditer(
            r"@import\s+(?:url\(\s*)?['\"]([^'\"]+)['\"]", source, re.I
        )
    )
    return resources


def validate_html(path: Path) -> ValidationResult:
    findings: list[Finding] = []
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return ValidationResult(
            (_finding("error", "file-not-found", f"HTML file not found: {path}"),)
        )

    if len(raw) > MAX_BYTES:
        findings.append(
            _finding("error", "file-too-large", f"HTML file exceeds {MAX_BYTES} bytes")
        )

    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return ValidationResult(
            (_finding("error", "invalid-utf8", "HTML file must be valid UTF-8"),)
        )

    parser = _PreflightParser()
    parser.feed(source)
    parser.close()

    if {"html", "head", "body"} - parser.seen:
        findings.append(
            _finding(
                "error",
                "incomplete-document",
                "Document must include html, head, and body elements",
            )
        )
    if not parser.doctype_html:
        findings.append(
            _finding(
                "warning", "missing-doctype", "Document should declare HTML5 doctype"
            )
        )

    charset = parser.meta.get("charset", "").strip().lower()
    if charset != "utf-8":
        findings.append(
            _finding("error", "invalid-charset", "Document charset must be utf-8")
        )
    if parser.meta.get("use-iframe", "").strip().lower() != "true":
        findings.append(
            _finding("error", "invalid-iframe-mode", "Meta use-iframe must be true")
        )
    height_mode = parser.meta.get("html-box-height-mode", "").strip().lower()
    if height_mode not in HEIGHT_MODES:
        findings.append(
            _finding(
                "error",
                "invalid-height-mode",
                "Meta html-box-height-mode must be auto or viewport",
            )
        )

    viewport = parser.meta.get("viewport", "").lower()
    if "width=device-width" not in viewport:
        findings.append(
            _finding(
                "warning",
                "nonresponsive-viewport",
                "Viewport should include width=device-width",
            )
        )
    if not parser.meta.get("description", "").strip():
        findings.append(
            _finding(
                "warning", "missing-description", "Add a reader-facing description"
            )
        )
    if not "".join(parser.title_text).strip():
        findings.append(_finding("warning", "missing-title", "Add a document title"))

    resource_kinds = {
        kind
        for value in [*parser.resources, *_resource_values(source)]
        for kind in [_resource_kind(value)]
        if kind is not None
    }
    if "external" in resource_kinds:
        findings.append(
            _finding(
                "warning", "external-resource", "Document uses an external resource"
            )
        )
    if "relative" in resource_kinds:
        findings.append(
            _finding(
                "warning",
                "relative-resource",
                "Relative resources may not survive html5-block embedding",
            )
        )
    if re.search(
        r"(?:api[_-]?key|secret|token|password)\s*[:=]\s*[^\s<]+",
        source,
        re.I,
    ):
        findings.append(
            _finding(
                "warning", "secret-like-content", "Review possible sensitive content"
            )
        )

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
