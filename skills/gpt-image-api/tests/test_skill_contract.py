from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[1]


class SkillContractTests(unittest.TestCase):
    def test_skill_entrypoint_is_current_model_only_and_progressive(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: gpt-image-api", text)
        self.assertIn("description: Use when", text)
        self.assertIn("gpt-image-2.5-flare", text)
        self.assertIn("gpt-image-2.5-sunburst", text)
        self.assertIsNone(re.search(r"gpt-image-2(?![.-]5)", text))
        self.assertLess(len(text.split()), 900)

    def test_entrypoint_routes_to_mode_specific_references(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for name in (
            "model-selection.md",
            "image-api.md",
            "generation.md",
            "editing.md",
            "prompting.md",
            "sample-prompts.md",
            "community-practices.md",
            "official-links.md",
        ):
            with self.subTest(name=name):
                self.assertIn(name, text)
                self.assertTrue((SKILL_DIR / "references" / name).is_file())

    def test_published_skill_does_not_reference_system_imagegen(self):
        published = []
        paths = [
            SKILL_DIR / "SKILL.md",
            *(SKILL_DIR / "references").glob("*.md"),
            SKILL_DIR / "scripts" / "gpt_image_api.py",
        ]
        for path in paths:
            published.append(path.read_text(encoding="utf-8"))
        text = "\n".join(published).lower()
        self.assertNotIn("$imagegen", text)
        self.assertNotIn("system imagegen", text)
        self.assertNotIn("built-in image_gen", text)
        self.assertIsNone(re.search(r"gpt-image-2(?![.-]5)", text))

    def test_cli_and_eval_contract_are_present(self):
        self.assertTrue((SKILL_DIR / "scripts" / "gpt_image_api.py").is_file())
        evals = json.loads((SKILL_DIR / "evals" / "evals.json").read_text())
        self.assertEqual(evals["skill_name"], "gpt-image-api")
        self.assertGreaterEqual(len(evals["evals"]), 4)

    def test_catalogs_publish_new_name_and_remove_old_skill_name(self):
        for relative in (
            "docs/skills-catalog.en.md",
            "docs/skills-catalog.zh-CN.md",
        ):
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn("gpt-image-api", text)
                self.assertNotIn("--skill gpt-image-2`", text)


if __name__ == "__main__":
    unittest.main()
