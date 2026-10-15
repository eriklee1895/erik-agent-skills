"""Exercise the design helper interface and self-contained reference resources."""

import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ThemeContractTests(unittest.TestCase):
    def test_design_reference_links_resolve_locally(self):
        for name in ("theme-routing.md", "visual-system.md", "palettes.md"):
            reference = ROOT / "references" / name
            for target in re.findall(r"\]\(([^)]+)\)", reference.read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(reference=name, target=target):
                    self.assertTrue((reference.parent / target.split("#")[0]).exists())

    def test_catalog_svg_examples_are_parseable_resources(self):
        catalog = ROOT / "references" / "palettes.md"
        examples = re.findall(r"\]\(([^)]+\.svg)\)", catalog.read_text())
        self.assertTrue(examples)
        for target in examples:
            with self.subTest(target=target):
                svg = ET.parse(catalog.parent / target).getroot()
                self.assertEqual("svg", svg.tag.rsplit("}", 1)[-1])

    def test_cli_accepts_agent_palette_without_overriding_brand_identity(self):
        script = str(ROOT / "scripts" / "theme_router.py")
        for extra, expected in (([], "custom-plum-stone"),
                                (["--brand-theme", "brand-teal"], "brand-teal")):
            with self.subTest(extra=extra):
                completed = subprocess.run(
                    [sys.executable, script, "--purpose", "benchmark",
                     "--theme", "custom-plum-stone", *extra],
                    text=True, capture_output=True, check=True,
                )
                self.assertEqual(expected, completed.stdout.strip())


if __name__ == "__main__":
    unittest.main()
