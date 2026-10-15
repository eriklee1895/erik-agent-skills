import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "theme_router.py"
SPEC = importlib.util.spec_from_file_location("theme_router", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ThemeRouterTests(unittest.TestCase):
    def test_explicit_user_theme_has_highest_precedence(self):
        self.assertEqual(
            "riso-brut",
            MODULE.resolve_theme(
                user_theme="riso-brut",
                brand_theme="grove",
                existing_theme="white-report",
                diagram_purpose="architecture",
                article_tone="technical",
            ),
        )

    def test_existing_theme_is_preserved_for_revision(self):
        self.assertEqual(
            "grove",
            MODULE.resolve_theme(
                existing_theme="grove",
                diagram_purpose="architecture",
                article_tone="technical",
            ),
        )

    def test_purpose_routes_are_deterministic(self):
        cases = {
            "architecture": "light-technical",
            "process": "light-technical",
            "state": "light-technical",
            "benchmark": "white-report",
            "comparison": "riptide-cobalt",
            "quadrant": "grove",
            "focus-detail": "avocado-press",
        }
        for purpose, expected in cases.items():
            with self.subTest(purpose=purpose):
                self.assertEqual(
                    expected,
                    MODULE.resolve_theme(
                        diagram_purpose=purpose,
                        article_tone="technical",
                    ),
                )

    def test_timeline_and_creative_tone_route_to_coral(self):
        self.assertEqual(
            "coral",
            MODULE.resolve_theme(
                diagram_purpose="timeline",
                article_tone="creative",
            ),
        )

    def test_benchmark_tone_overrides_generic_comparison_theme(self):
        self.assertEqual(
            "white-report",
            MODULE.resolve_theme(
                diagram_purpose="comparison",
                article_tone="benchmark",
            ),
        )

    def test_benchmark_tone_does_not_override_architecture_purpose(self):
        self.assertEqual(
            "light-technical",
            MODULE.resolve_theme(
                diagram_purpose="architecture",
                article_tone="benchmark",
            ),
        )

    def test_unknown_inputs_use_light_technical(self):
        self.assertEqual("light-technical", MODULE.resolve_theme())

    def test_agent_choice_can_use_a_custom_palette_for_architecture(self):
        self.assertEqual(
            "custom-plum-stone",
            MODULE.resolve_theme(
                selected_theme="custom-plum-stone",
                diagram_purpose="architecture",
                article_tone="technical",
            ),
        )

    def test_agent_choice_does_not_override_user_brand_or_existing_identity(self):
        for key in ("user_theme", "brand_theme", "existing_theme"):
            with self.subTest(authority=key):
                self.assertEqual(
                    "brand-teal",
                    MODULE.resolve_theme(
                        **{key: "brand-teal"},
                        selected_theme="white-report",
                        diagram_purpose="benchmark",
                    ),
                )

    def test_article_tone_informs_suggestion_without_a_selected_theme(self):
        self.assertEqual(
            "grove",
            MODULE.resolve_theme(
                diagram_purpose="architecture", article_tone="governance"
            ),
        )

    def test_agent_choice_can_adapt_a_benchmark_to_its_article(self):
        self.assertEqual(
            "custom-teal-report",
            MODULE.resolve_theme(
                selected_theme="custom-teal-report",
                diagram_purpose="benchmark", article_tone="benchmark",
            ),
        )


if __name__ == "__main__":
    unittest.main()
