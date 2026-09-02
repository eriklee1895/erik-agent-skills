import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_html_block.py"
SPEC = importlib.util.spec_from_file_location("validate_html_block", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


VALID = """<!doctype html><html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="use-iframe" content="true">
<meta name="html-box-height-mode" content="auto">
<meta name="description" content="验证示例">
<title>验证示例</title></head><body><main>ok</main></body></html>"""


class ValidateHtmlBlockTests(unittest.TestCase):
    def validate(self, html: str) -> object:
        return self.validate_bytes(html.encode("utf-8"))

    def validate_bytes(self, content: bytes) -> object:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "diagram.html"
            path.write_bytes(content)
            return MODULE.validate_html(path)

    def test_valid_self_contained_auto_document_passes(self):
        result = self.validate(VALID)
        self.assertTrue(result.ok)
        self.assertEqual((), result.findings)

    def test_missing_required_meta_is_an_error(self):
        result = self.validate(VALID.replace('name="viewport"', 'name="not-viewport"'))
        self.assertIn("missing-meta", {finding.code for finding in result.findings})
        self.assertFalse(result.ok)

    def test_invalid_utf8_is_a_stable_error(self):
        result = self.validate_bytes(VALID.encode("utf-8") + b"\xff")
        self.assertEqual(
            [("error", "invalid-utf8", "HTML file must be valid UTF-8")],
            [
                (finding.level, finding.code, finding.message)
                for finding in result.findings
            ],
        )
        self.assertFalse(result.ok)

    def test_document_fragment_is_an_error(self):
        result = self.validate("<main>not a complete document</main>")
        self.assertIn(
            "incomplete-document", {finding.code for finding in result.findings}
        )
        self.assertFalse(result.ok)

    def test_unclosed_body_is_an_error(self):
        result = self.validate(VALID.replace("</body>", ""))
        self.assertIn(
            "incomplete-document", {finding.code for finding in result.findings}
        )
        self.assertFalse(result.ok)

    def test_self_closing_void_element_does_not_break_complete_document(self):
        result = self.validate(
            VALID.replace(
                "<main>ok</main>",
                '<main><img src="data:image/svg+xml,%3Csvg/%3E" alt=""/></main>',
            )
        )
        self.assertTrue(result.ok)
        self.assertNotIn(
            "incomplete-document", {finding.code for finding in result.findings}
        )

    def test_contract_metadata_outside_head_is_an_error(self):
        description = '<meta name="description" content="验证示例">'
        result = self.validate(
            VALID.replace(description, "").replace("<body>", f"<body>{description}")
        )
        codes = {finding.code for finding in result.findings}
        self.assertIn("misplaced-meta", codes)
        self.assertIn("missing-description", codes)
        self.assertFalse(result.ok)

    def test_missing_title_in_head_is_an_error(self):
        result = self.validate(VALID.replace("<title>验证示例</title>", ""))
        self.assertIn("missing-title", {finding.code for finding in result.findings})
        self.assertFalse(result.ok)

    def test_charset_must_be_utf8(self):
        result = self.validate(VALID.replace('charset="utf-8"', 'charset="iso-8859-1"'))
        self.assertIn("invalid-charset", {finding.code for finding in result.findings})
        self.assertFalse(result.ok)

    def test_file_larger_than_500_kib_is_an_error(self):
        result = self.validate(VALID + "x" * (500 * 1024))
        self.assertIn("file-too-large", {finding.code for finding in result.findings})
        self.assertFalse(result.ok)

    def test_unknown_height_mode_is_an_error(self):
        result = self.validate(VALID.replace('content="auto"', 'content="fixed"'))
        self.assertIn(
            "invalid-height-mode", {finding.code for finding in result.findings}
        )
        self.assertFalse(result.ok)

    def test_missing_height_mode_is_an_error(self):
        result = self.validate(
            VALID.replace('<meta name="html-box-height-mode" content="auto">\n', "")
        )
        self.assertIn(
            "invalid-height-mode", {finding.code for finding in result.findings}
        )
        self.assertFalse(result.ok)

    def test_remote_script_is_a_warning_not_an_error(self):
        result = self.validate(
            VALID.replace(
                "</body>", '<script src="https://example.com/a.js"></script></body>'
            )
        )
        self.assertIn(
            "external-resource", {finding.code for finding in result.findings}
        )
        self.assertTrue(result.ok)

    def test_relative_resource_attribute_is_a_warning_not_an_error(self):
        result = self.validate(
            VALID.replace("</body>", '<img src="./missing.png" alt=""></body>')
        )
        self.assertIn(
            "relative-resource", {finding.code for finding in result.findings}
        )
        self.assertTrue(result.ok)

    def test_additional_resource_bearing_attributes_are_checked(self):
        html = VALID.replace(
            "</body>",
            '<video poster="/poster.png"></video>'
            '<img srcset="local.png 1x, https://example.com/remote.png 2x" alt="">'
            '<object data="asset.svg"></object></body>',
        )
        result = self.validate(html)
        codes = {finding.code for finding in result.findings}
        self.assertIn("relative-resource", codes)
        self.assertIn("external-resource", codes)
        self.assertTrue(result.ok)

    def test_remote_svg_image_href_is_a_warning_not_an_error(self):
        result = self.validate(
            VALID.replace(
                "</body>",
                '<svg><image href="https://example.com/a.png"/></svg></body>',
            )
        )
        self.assertIn(
            "external-resource", {finding.code for finding in result.findings}
        )
        self.assertTrue(result.ok)

    def test_relative_svg_use_href_is_a_warning_not_an_error(self):
        result = self.validate(
            VALID.replace(
                "</body>",
                '<svg><use href="./icons.svg#symbol"/></svg></body>',
            )
        )
        self.assertIn(
            "relative-resource", {finding.code for finding in result.findings}
        )
        self.assertTrue(result.ok)

    def test_svg_feimage_xlink_href_is_checked_case_insensitively(self):
        result = self.validate(
            VALID.replace(
                "</body>",
                '<svg><filter><feImage xlink:href="https://example.com/filter.png"/></filter></svg></body>',
            )
        )
        self.assertIn(
            "external-resource", {finding.code for finding in result.findings}
        )
        self.assertTrue(result.ok)

    def test_internal_svg_fragment_hrefs_are_not_resource_warnings(self):
        html = VALID.replace(
            "</body>",
            '<svg><symbol id="symbol"/><filter id="filter"/>'
            '<image href="#symbol"/><use xlink:href="#symbol"/>'
            '<feImage href="#filter"/></svg></body>',
        )
        result = self.validate(html)
        codes = {finding.code for finding in result.findings}
        self.assertNotIn("external-resource", codes)
        self.assertNotIn("relative-resource", codes)
        self.assertTrue(result.ok)

    def test_css_url_and_import_are_resource_warnings(self):
        css = """<style>
        @import "https://example.com/theme.css";
        .hero { background-image: url('./hero.png'); }
        </style>"""
        result = self.validate(VALID.replace("</head>", f"{css}</head>"))
        codes = {finding.code for finding in result.findings}
        self.assertIn("relative-resource", codes)
        self.assertIn("external-resource", codes)
        self.assertTrue(result.ok)

    def test_javascript_fetch_is_a_network_call_warning(self):
        result = self.validate(
            VALID.replace("</body>", '<script>fetch("/api/data")</script></body>')
        )
        self.assertIn("network-call", {finding.code for finding in result.findings})
        self.assertTrue(result.ok)

    def test_animation_without_reduced_motion_is_a_warning(self):
        result = self.validate(
            VALID.replace(
                "</head>", "<style>.box { animation: spin 1s; }</style></head>"
            )
        )
        self.assertIn(
            "missing-reduced-motion", {finding.code for finding in result.findings}
        )
        self.assertTrue(result.ok)

    def test_svg_animation_without_reduced_motion_is_a_warning(self):
        result = self.validate(
            VALID.replace(
                "</body>",
                '<svg><circle><animate attributeName="r" values="1;2"/></circle></svg></body>',
            )
        )
        self.assertIn(
            "missing-reduced-motion", {finding.code for finding in result.findings}
        )
        self.assertTrue(result.ok)

    def test_request_animation_frame_without_reduced_motion_is_a_warning(self):
        result = self.validate(
            VALID.replace(
                "</body>", "<script>requestAnimationFrame(draw)</script></body>"
            )
        )
        self.assertIn(
            "missing-reduced-motion", {finding.code for finding in result.findings}
        )
        self.assertTrue(result.ok)

    def test_large_inline_dataset_is_a_warning_not_an_error(self):
        dataset = "x" * (50 * 1024)
        result = self.validate(
            VALID.replace(
                "</body>",
                f'<script type="application/json">{{"data":"{dataset}"}}</script></body>',
            )
        )
        self.assertIn(
            "large-inline-dataset", {finding.code for finding in result.findings}
        )
        self.assertTrue(result.ok)

    def test_inline_dataset_below_threshold_has_no_size_warning(self):
        dataset = "x" * (50 * 1024 - 100)
        result = self.validate(
            VALID.replace(
                "</body>",
                f'<script type="application/json">{{"data":"{dataset}"}}</script></body>',
            )
        )
        self.assertNotIn(
            "large-inline-dataset", {finding.code for finding in result.findings}
        )

    def test_inline_base64_and_secret_like_values_are_warnings(self):
        html = VALID.replace(
            "</body>",
            '<img src="data:image/png;base64,AAAA">'
            "<p>api_key=sk-test-1234567890</p></body>",
        )
        result = self.validate(html)
        codes = {finding.code for finding in result.findings}
        self.assertIn("inline-base64", codes)
        self.assertIn("secret-like-content", codes)
        self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
