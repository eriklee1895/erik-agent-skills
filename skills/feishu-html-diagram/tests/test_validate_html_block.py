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
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "diagram.html"
            path.write_text(html, encoding="utf-8")
            return MODULE.validate_html(path)

    def test_valid_self_contained_auto_document_passes(self):
        result = self.validate(VALID)
        self.assertTrue(result.ok)
        self.assertEqual((), result.findings)

    def test_missing_required_meta_is_an_error(self):
        result = self.validate(VALID.replace('name="viewport"', 'name="not-viewport"'))
        self.assertIn("missing-meta", {finding.code for finding in result.findings})
        self.assertFalse(result.ok)

    def test_file_larger_than_500_kib_is_an_error(self):
        result = self.validate(VALID + "x" * (500 * 1024))
        self.assertIn("file-too-large", {finding.code for finding in result.findings})
        self.assertFalse(result.ok)

    def test_unknown_height_mode_is_an_error(self):
        result = self.validate(VALID.replace('content="auto"', 'content="fixed"'))
        self.assertIn("invalid-height-mode", {finding.code for finding in result.findings})
        self.assertFalse(result.ok)

    def test_remote_script_is_a_warning_not_an_error(self):
        result = self.validate(VALID.replace("</body>", '<script src="https://example.com/a.js"></script></body>'))
        self.assertIn("external-resource", {finding.code for finding in result.findings})
        self.assertTrue(result.ok)

    def test_animation_without_reduced_motion_is_a_warning(self):
        result = self.validate(VALID.replace("</head>", "<style>.box { animation: spin 1s; }</style></head>"))
        self.assertIn("missing-reduced-motion", {finding.code for finding in result.findings})
        self.assertTrue(result.ok)

    def test_inline_base64_and_secret_like_values_are_warnings(self):
        html = VALID.replace(
            "</body>",
            '<img src="data:image/png;base64,AAAA">'
            '<p>api_key=sk-test-1234567890</p></body>',
        )
        result = self.validate(html)
        codes = {finding.code for finding in result.findings}
        self.assertIn("inline-base64", codes)
        self.assertIn("secret-like-content", codes)
        self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
