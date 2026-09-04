import importlib.util
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).parents[1]
TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"
SCRIPT = SKILL_DIR / "scripts" / "validate_html_block.py"
SPEC = importlib.util.spec_from_file_location("template_preflight", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TemplateAssetTests(unittest.TestCase):
    def test_high_risk_visual_patterns_ship_as_valid_templates(self):
        for name in (
            "tabbed-animated-architecture.html",
            "threejs-embedded-scene.html",
        ):
            with self.subTest(name=name):
                path = TEMPLATE_DIR / name
                self.assertTrue(path.is_file(), f"missing template: {name}")

                result = MODULE.validate_html(path)

                self.assertTrue(result.ok, result.findings)


if __name__ == "__main__":
    unittest.main()
