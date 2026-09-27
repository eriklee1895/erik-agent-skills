import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "fit_check.py"
SPEC = importlib.util.spec_from_file_location("fit_check", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FitCheckTests(unittest.TestCase):
    def check(self, svg: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "diagram.svg"
            path.write_text(svg, encoding="utf-8")
            return MODULE.check_svg_fit(path)

    def test_accepts_tight_content_with_eighty_pixel_air(self):
        result = self.check(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 240">
              <rect x="80" y="80" width="240" height="80" fill="#FFFFFF"/>
              <text x="100" y="126" font-size="20">架构</text>
            </svg>'''
        )
        self.assertTrue(result.ok, result.findings)
        self.assertEqual((), result.findings)

    def test_reports_canvas_bleed_as_an_error(self):
        result = self.check(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 240">
              <rect x="-4" y="80" width="240" height="80" fill="#FFFFFF"/>
            </svg>'''
        )
        self.assertFalse(result.ok)
        self.assertIn("canvas-bleed", {finding.code for finding in result.findings})

    def test_reports_large_bottom_deadspace_as_a_warning(self):
        result = self.check(
            '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
              <rect x="80" y="80" width="240" height="100" fill="#FFFFFF"/>
            </svg>'''
        )
        self.assertTrue(result.ok, result.findings)
        self.assertIn("deadspace-bottom", {finding.code for finding in result.findings})


if __name__ == "__main__":
    unittest.main()
