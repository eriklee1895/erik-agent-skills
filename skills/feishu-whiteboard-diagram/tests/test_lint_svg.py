import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "lint_svg.py"
SPEC = importlib.util.spec_from_file_location("lint_svg", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


MINIMAL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="4"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0 0 L10 4 L0 8 z"/>
    </marker>
  </defs>
  <rect x="20" y="40" width="120" height="48" rx="12" fill="#DBEAFE" stroke="#2563EB" stroke-width="2"/>
  <text x="80" y="70" text-anchor="middle" font-size="14" fill="#1F2329">步骤</text>
  <line x1="140" y1="64" x2="220" y2="64" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow)"/>
</svg>
"""


class LintSvgTests(unittest.TestCase):
    def validate(self, svg: str):
        return self.validate_bytes(svg.encode("utf-8"))

    def validate_bytes(self, content: bytes):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "diagram.svg"
            path.write_bytes(content)
            return MODULE.validate_svg(path)

    def test_minimal_svg_passes(self):
        result = self.validate(MINIMAL)
        self.assertTrue(result.ok, result.findings)
        self.assertEqual((), result.findings)

    def test_missing_file(self):
        result = MODULE.validate_svg(Path("/missing/diagram.svg"))
        self.assertFalse(result.ok)
        self.assertEqual("file-not-found", result.findings[0].code)

    def test_invalid_utf8(self):
        result = self.validate_bytes(MINIMAL.encode("utf-8") + b"\xff")
        self.assertFalse(result.ok)
        self.assertEqual("invalid-utf8", result.findings[0].code)

    def test_missing_viewbox(self):
        result = self.validate(MINIMAL.replace(' viewBox="0 0 400 200"', ""))
        self.assertFalse(result.ok)
        self.assertIn("missing-viewbox", {f.code for f in result.findings})

    def test_clippath_is_error(self):
        result = self.validate(
            MINIMAL.replace(
                "</svg>",
                '<clipPath id="c"><rect x="0" y="0" width="10" height="10"/></clipPath></svg>',
            )
        )
        self.assertFalse(result.ok)
        self.assertIn("unsupported-tag", {f.code for f in result.findings})

    def test_font_family_is_error(self):
        result = self.validate(
            MINIMAL.replace(
                'fill="#1F2329">步骤</text>',
                'fill="#1F2329" font-family="Arial">步骤</text>',
            )
        )
        self.assertFalse(result.ok)
        self.assertIn("font-family", {f.code for f in result.findings})

    def test_opacity_is_warning(self):
        result = self.validate(
            MINIMAL.replace(
                'fill="#DBEAFE"',
                'fill="#DBEAFE" opacity="0.4"',
            )
        )
        self.assertTrue(result.ok)
        self.assertIn("opacity", {f.code for f in result.findings})

    def test_polygon_diamond_is_flatten_warning(self):
        result = self.validate(
            MINIMAL.replace(
                "</svg>",
                '<polygon points="80,120 110,150 80,180 50,150" fill="#FFF7ED" stroke="#EA580C"/></svg>',
            )
        )
        self.assertTrue(result.ok)
        self.assertIn("flatten-to-svg-node", {f.code for f in result.findings})

    def test_marker_path_is_not_flatten_warning(self):
        result = self.validate(MINIMAL)
        self.assertEqual((), result.findings)

    def test_each_declared_edge_requires_an_arrow_marker(self):
        result = self.validate(
            MINIMAL.replace(
                "</svg>",
                '<line data-role="edge" x1="20" y1="120" x2="140" y2="120"/></svg>',
            )
        )
        self.assertFalse(result.ok)
        self.assertIn("missing-marker-end", {f.code for f in result.findings})

    def test_marker_reference_must_exist(self):
        result = self.validate(MINIMAL.replace("url(#arrow)", "url(#missing)"))
        self.assertFalse(result.ok)
        self.assertIn("missing-marker-reference", {f.code for f in result.findings})

    def test_undirected_spoke_does_not_require_an_arrow(self):
        result = self.validate(
            MINIMAL.replace(
                '<line x1="140" y1="64" x2="220" y2="64" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow)"/>',
                '<line data-role="spoke" x1="140" y1="64" x2="220" y2="64" stroke="#94A3B8" stroke-width="2"/>',
            )
        )
        self.assertEqual((), result.findings)

    def test_curve_path_with_marker_is_a_connector_not_a_flatten_warning(self):
        result = self.validate(
            MINIMAL.replace(
                '<line x1="140" y1="64" x2="220" y2="64" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow)"/>',
                '<path data-role="edge" d="M140 64 C170 64 190 96 220 96" fill="none" stroke="#94A3B8" marker-end="url(#arrow)"/>',
            )
        )
        self.assertNotIn("flatten-to-svg-node", {f.code for f in result.findings})

    def test_low_contrast_declared_background_is_error(self):
        result = self.validate(
            MINIMAL.replace(
                'fill="#1F2329">步骤</text>',
                'fill="#EFE9D9" data-bg="#E85A1F">步骤</text>',
            )
        )
        self.assertFalse(result.ok)
        self.assertIn("low-contrast", {f.code for f in result.findings})

    def test_accessible_declared_background_passes(self):
        result = self.validate(
            MINIMAL.replace(
                'fill="#1F2329">步骤</text>',
                'fill="#0F0F0F" data-bg="#E85A1F">步骤</text>',
            )
        )
        self.assertNotIn("low-contrast", {f.code for f in result.findings})


if __name__ == "__main__":
    unittest.main()
