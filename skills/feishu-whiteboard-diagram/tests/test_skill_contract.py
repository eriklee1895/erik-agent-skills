import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillContractTests(unittest.TestCase):
    def test_runtime_dependencies_include_python_and_node(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('bins: ["node", "npx", "python3"]', skill)

    def test_utf8_guidance_does_not_reference_undefined_src(self):
        guidance = (ROOT / "references" / "write-verify.md").read_text(encoding="utf-8")
        self.assertNotIn("write_text(src", guidance)

    def test_third_party_notice_is_linked_from_entrypoint(self):
        notice = ROOT / "THIRD_PARTY_NOTICES.md"
        self.assertTrue(notice.exists())
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("THIRD_PARTY_NOTICES.md", skill)

    def test_visual_contract_links_theme_routing_and_fit_check(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("theme-routing.md", skill)
        self.assertTrue((ROOT / "references" / "theme-routing.md").exists())
        self.assertTrue((ROOT / "references" / "community-practice.md").exists())
        self.assertTrue((ROOT / "scripts" / "fit_check.py").exists())


if __name__ == "__main__":
    unittest.main()
