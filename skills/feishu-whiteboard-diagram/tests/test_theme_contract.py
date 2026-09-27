import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ThemeContractTests(unittest.TestCase):
    def setUp(self):
        self.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.routing = (ROOT / "references" / "theme-routing.md").read_text(
            encoding="utf-8"
        )
        self.visual = (ROOT / "references" / "visual-system.md").read_text(
            encoding="utf-8"
        )

    def test_light_technical_is_the_architecture_default(self):
        self.assertIn("light-technical", self.routing)
        self.assertIn("技术架构", self.routing)
        self.assertIn("#F8FAFC", self.routing)
        self.assertIn("默认主题", self.visual)
        self.assertIn("scripts/theme_router.py", self.routing)

    def test_theme_selection_has_explicit_precedence(self):
        self.assertIn("品牌 / 用户明确指定", self.routing)
        self.assertIn("图的语义", self.routing)
        self.assertIn("文章主题", self.routing)
        self.assertIn("light-technical", self.skill)

    def test_riso_is_explicitly_editorial_not_the_architecture_fallback(self):
        self.assertIn("Riso Brut", self.routing)
        self.assertIn("编辑型", self.routing)
        self.assertNotIn("技术架构默认使用 Riso Brut", self.routing)


if __name__ == "__main__":
    unittest.main()
