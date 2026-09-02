"""Deterministic checks for self-contained Feishu html5-block documents."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

REQUIRED_META = {
    "viewport": "width=device-width, initial-scale=1",
    "use-iframe": "true",
}
HEIGHT_MODES = {"auto", "viewport"}
MAX_BYTES = 500 * 1024
INLINE_DATASET_WARNING_BYTES = 50 * 1024
CONTRACT_META_NAMES = {*REQUIRED_META, "html-box-height-mode", "description"}
VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
RESOURCE_ATTRIBUTES = {
    "audio": ("src",),
    "embed": ("src",),
    "feimage": ("href", "xlink:href"),
    "iframe": ("src",),
    "image": ("href", "xlink:href"),
    "img": ("src", "srcset"),
    "input": ("src",),
    "link": ("href",),
    "object": ("data",),
    "script": ("src",),
    "source": ("src", "srcset"),
    "track": ("src",),
    "use": ("href", "xlink:href"),
    "video": ("src", "poster"),
}
INLINE_DATASET_TYPES = {
    "application/json",
    "application/ld+json",
    "text/json",
    "text/csv",
    "application/csv",
}


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
        self.doctype_html = False
        self.starts: Counter[str] = Counter()
        self.ends: Counter[str] = Counter()
        self.parents: dict[str, list[str | None]] = {"html": [], "head": [], "body": []}
        self.stack: list[str] = []
        self.malformed_structure = False
        self.misplaced_meta = False
        self.title: list[str] = []
        self.script_text: list[str] = []
        self.inline_datasets: list[list[str]] = []
        self.current_inline_dataset: list[str] | None = None

    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower() == "doctype html":
            self.doctype_html = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = dict(attrs)
        if tag in self.parents:
            self.starts[tag] += 1
            self.parents[tag].append(self.stack[-1] if self.stack else None)
        if tag == "meta":
            name = values.get("name")
            normalized_name = name.lower() if name else None
            is_contract_meta = (
                "charset" in values or normalized_name in CONTRACT_META_NAMES
            )
            if "head" in self.stack:
                if "charset" in values:
                    self.meta["charset"] = values.get("charset") or ""
                if normalized_name:
                    self.meta[normalized_name] = values.get("content", "") or ""
            elif is_contract_meta:
                self.misplaced_meta = True
        if (
            tag == "script"
            and (values.get("type") or "").lower().split(";", 1)[0].strip()
            in INLINE_DATASET_TYPES
        ):
            self.current_inline_dataset = []
            self.inline_datasets.append(self.current_inline_dataset)
        for attribute in RESOURCE_ATTRIBUTES.get(tag, ()):
            value = values.get(attribute)
            if value:
                if attribute == "srcset":
                    self.resources.extend(
                        (tag, candidate.strip().split(maxsplit=1)[0])
                        for candidate in value.split(",")
                        if candidate.strip()
                    )
                else:
                    self.resources.append((tag, value))
        if tag not in VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "script":
            self.current_inline_dataset = None
        if tag in self.parents:
            self.ends[tag] += 1
        if not self.stack or self.stack[-1] != tag:
            self.malformed_structure = True
            return
        self.stack.pop()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self.stack and self.stack[-1] == "title" and "head" in self.stack:
            self.title.append(data)
        if self.stack and self.stack[-1] == "script":
            self.script_text.append(data)
            if self.current_inline_dataset is not None:
                self.current_inline_dataset.append(data)

    @property
    def complete_document(self) -> bool:
        return (
            self.doctype_html
            and all(
                self.starts[tag] == 1 and self.ends[tag] == 1
                for tag in ("html", "head", "body")
            )
            and self.parents["html"] == [None]
            and self.parents["head"] == ["html"]
            and self.parents["body"] == ["html"]
            and not self.stack
            and not self.malformed_structure
        )


def _finding(level: str, code: str, message: str) -> Finding:
    return Finding(level=level, code=code, message=message)


def _resource_kind(value: str) -> str | None:
    normalized = value.strip().lower()
    if not normalized or normalized.startswith(("#", "data:", "blob:", "javascript:")):
        return None
    if normalized.startswith(("http://", "https://", "//")):
        return "remote"
    if re.match(r"^[a-z][a-z0-9+.-]*:", normalized):
        return None
    return "relative"


def _css_resources(source: str) -> list[str]:
    values = [
        match.group(2).strip()
        for match in re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)", source, re.IGNORECASE)
    ]
    values.extend(
        match.group(1)
        for match in re.finditer(
            r"@import\s+(?:url\(\s*)?['\"]([^'\"]+)['\"]", source, re.IGNORECASE
        )
    )
    return values


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

    parser = _DocumentParser()
    parser.feed(source)
    parser.close()

    if not parser.complete_document:
        findings.append(
            _finding(
                "error",
                "incomplete-document",
                "Document must include complete <!doctype html>, <html>, <head>, and <body> structure",
            )
        )
    if parser.misplaced_meta:
        findings.append(
            _finding(
                "error", "misplaced-meta", "Contract metadata must be inside <head>"
            )
        )

    if "charset" not in parser.meta:
        findings.append(
            _finding("error", "missing-charset", "Document must declare a charset")
        )
    elif parser.meta["charset"].strip().lower() != "utf-8":
        findings.append(
            _finding("error", "invalid-charset", "Document charset must be utf-8")
        )
    for name, expected in REQUIRED_META.items():
        if parser.meta.get(name) != expected:
            findings.append(
                _finding("error", "missing-meta", f"Meta {name!r} must be {expected!r}")
            )
    height_mode = parser.meta.get("html-box-height-mode")
    if height_mode not in HEIGHT_MODES:
        message = (
            "Missing html-box-height-mode meta"
            if height_mode is None
            else f"Unknown height mode: {height_mode}"
        )
        findings.append(_finding("error", "invalid-height-mode", message))
    if not parser.meta.get("description", "").strip():
        findings.append(
            _finding(
                "error", "missing-description", "Document must declare a description"
            )
        )
    if not "".join(parser.title).strip():
        findings.append(
            _finding(
                "error", "missing-title", "Document must declare a title inside <head>"
            )
        )

    resource_kinds = {
        kind
        for _, value in parser.resources
        for kind in [_resource_kind(value)]
        if kind is not None
    }
    resource_kinds.update(
        kind
        for value in _css_resources(source)
        for kind in [_resource_kind(value)]
        if kind is not None
    )
    if "remote" in resource_kinds:
        findings.append(
            _finding(
                "warning",
                "external-resource",
                "Document references an external resource",
            )
        )
    if "relative" in resource_kinds:
        findings.append(
            _finding(
                "warning",
                "relative-resource",
                "Document references a relative resource that may not survive embedding",
            )
        )
    scripts = "\n".join(parser.script_text)
    if re.search(
        r"\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\s*\(|\bnavigator\.sendBeacon\s*\(",
        scripts,
    ):
        findings.append(
            _finding(
                "warning", "network-call", "Document contains a JavaScript network call"
            )
        )
    if re.search(r"data:[^\s\"']+;base64,", source, re.IGNORECASE):
        findings.append(
            _finding("warning", "inline-base64", "Document contains inline base64 data")
        )
    if any(
        len("".join(dataset).encode("utf-8")) >= INLINE_DATASET_WARNING_BYTES
        for dataset in parser.inline_datasets
    ):
        findings.append(
            _finding(
                "warning",
                "large-inline-dataset",
                f"Document contains an inline dataset at or above {INLINE_DATASET_WARNING_BYTES // 1024} KiB",
            )
        )
    if re.search(
        r"(?:api[_-]?key|secret|token|password)\s*[:=]\s*[^\s<]+", source, re.IGNORECASE
    ):
        findings.append(
            _finding(
                "warning",
                "secret-like-content",
                "Document contains secret-like content",
            )
        )
    has_animation = (
        re.search(r"\banimation(?:-name)?\s*:|@keyframes\b", source, re.IGNORECASE)
        or re.search(r"<animate(?:motion|transform)?\b", source, re.IGNORECASE)
        or re.search(r"\brequestAnimationFrame\s*\(", scripts)
    )
    has_reduced_motion = re.search(r"prefers-reduced-motion", source, re.IGNORECASE)
    if has_animation and not has_reduced_motion:
        findings.append(
            _finding(
                "warning",
                "missing-reduced-motion",
                "Animation lacks reduced-motion handling",
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
