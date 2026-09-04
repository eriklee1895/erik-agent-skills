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
    def validate(self, html: str):
        return self.validate_bytes(html.encode("utf-8"))

    def validate_bytes(self, content: bytes):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "diagram.html"
            path.write_bytes(content)
            return MODULE.validate_html(path)

    def test_valid_self_contained_document_passes(self):
        result = self.validate(VALID)

        self.assertTrue(result.ok)
        self.assertEqual((), result.findings)

    def test_missing_file_is_an_error(self):
        result = MODULE.validate_html(Path("/missing/diagram.html"))

        self.assertFalse(result.ok)
        self.assertEqual("file-not-found", result.findings[0].code)

    def test_invalid_utf8_is_an_error(self):
        result = self.validate_bytes(VALID.encode("utf-8") + b"\xff")

        self.assertFalse(result.ok)
        self.assertEqual("invalid-utf8", result.findings[0].code)

    def test_file_over_500_kib_is_an_error(self):
        result = self.validate(VALID + "x" * (500 * 1024))

        self.assertFalse(result.ok)
        self.assertIn("file-too-large", {finding.code for finding in result.findings})

    def test_html_head_and_body_are_required(self):
        result = self.validate("<main>fragment</main>")

        self.assertFalse(result.ok)
        self.assertIn(
            "incomplete-document", {finding.code for finding in result.findings}
        )

    def test_platform_contract_metadata_is_required(self):
        cases = {
            "charset": (
                VALID.replace('charset="utf-8"', 'charset="latin-1"'),
                "invalid-charset",
            ),
            "iframe": (
                VALID.replace('content="true"', 'content="false"'),
                "invalid-iframe-mode",
            ),
            "height": (
                VALID.replace('content="auto"', 'content="fixed"'),
                "invalid-height-mode",
            ),
        }

        for label, (html, expected_code) in cases.items():
            with self.subTest(label=label):
                result = self.validate(html)
                self.assertFalse(result.ok)
                self.assertIn(
                    expected_code, {finding.code for finding in result.findings}
                )

    def test_missing_reader_metadata_is_a_warning(self):
        html = VALID.replace("<!doctype html>", "")
        html = html.replace(
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n', ""
        )
        html = html.replace('<meta name="description" content="验证示例">\n', "")
        html = html.replace("<title>验证示例</title>", "")

        result = self.validate(html)

        self.assertTrue(result.ok)
        self.assertEqual(
            {
                "missing-doctype",
                "nonresponsive-viewport",
                "missing-description",
                "missing-title",
            },
            {finding.code for finding in result.findings},
        )

    def test_equivalent_responsive_viewport_is_accepted(self):
        html = VALID.replace(
            'content="width=device-width, initial-scale=1"',
            'content="width=device-width, initial-scale=1.0, viewport-fit=cover"',
        )

        result = self.validate(html)

        self.assertTrue(result.ok)
        self.assertEqual((), result.findings)

    def test_browser_tolerated_optional_end_tags_are_not_rejected(self):
        html = VALID.replace("<main>ok</main>", "<main><p>第一段<p>第二段</main>")

        result = self.validate(html)

        self.assertTrue(result.ok)

    def test_external_and_relative_resources_are_warnings(self):
        html = VALID.replace(
            "</body>",
            '<style>.hero{background:url("./hero.png")}</style>'
            '<script src="https://example.com/chart.js"></script>'
            '<svg><use href="./icons.svg#flow"/></svg>'
            "</body>",
        )

        result = self.validate(html)

        self.assertTrue(result.ok)
        self.assertEqual(
            {"external-resource", "relative-resource"},
            {finding.code for finding in result.findings},
        )

    def test_embedded_data_and_internal_svg_refs_need_no_resource_warning(self):
        html = VALID.replace(
            "</body>",
            '<img src="data:image/png;base64,AAAA" alt="">'
            '<svg><use href="#flow"/></svg></body>',
        )

        result = self.validate(html)

        self.assertTrue(result.ok)
        self.assertEqual((), result.findings)

    def test_secret_like_content_is_a_review_warning(self):
        result = self.validate(
            VALID.replace("</body>", "<p>api_key=example</p></body>")
        )

        self.assertTrue(result.ok)
        self.assertEqual(
            {"secret-like-content"}, {finding.code for finding in result.findings}
        )

    def test_creative_web_techniques_are_outside_preflight_policy(self):
        html = VALID.replace(
            "</body>",
            "<style>@keyframes pulse{to{opacity:.5}}</style>"
            '<script>fetch("/data.json"); requestAnimationFrame(() => {});</script>'
            "</body>",
        )

        result = self.validate(html)

        self.assertTrue(result.ok)
        self.assertEqual((), result.findings)

    def test_javascript_data_variable_is_not_an_html_resource(self):
        html = VALID.replace(
            "</body>", '<script>const data = "./series.json";</script></body>'
        )

        result = self.validate(html)

        self.assertTrue(result.ok)
        self.assertEqual((), result.findings)


if __name__ == "__main__":
    unittest.main()
