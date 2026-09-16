from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[1]
TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"


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
            "template-selection.md",
            "community-practices.md",
            "official-links.md",
        ):
            with self.subTest(name=name):
                self.assertIn(name, text)
                self.assertTrue((SKILL_DIR / "references" / name).is_file())

        for name in (
            "generation-core.md",
            "editing-core.md",
            "layout-and-text.md",
            "characters-and-series.md",
            "brand-product-and-space.md",
        ):
            with self.subTest(name=name):
                self.assertIn(f"assets/templates/{name}", text)
                self.assertTrue((TEMPLATE_DIR / name).is_file())

        self.assertFalse((SKILL_DIR / "references" / "generation-recipes.md").exists())
        self.assertFalse((SKILL_DIR / "references" / "editing-recipes.md").exists())

    def test_template_selection_preserves_creative_freedom(self):
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        text = (SKILL_DIR / "references" / "template-selection.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("complete brief", text)
        self.assertIn("incomplete brief", text)
        self.assertIn("one template slice", text)
        self.assertIn("Do not stack", text)
        self.assertIn("unresolved placeholders", text)
        self.assertIn("Creative latitude", text)
        self.assertNotIn("sparse or specialized", skill_text)
        self.assertNotIn("sparse or specialized", text)
        self.assertIn("API parameter syntax", text)
        self.assertIn("transparency", text)
        self.assertIn("framing", text)

    def test_template_assets_have_reusable_contracts(self):
        template_count = 0
        for path in sorted(TEMPLATE_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            sections = re.split(r"(?m)^## ", text)[1:]
            template_count += len(sections)
            for section in sections:
                title = section.splitlines()[0]
                with self.subTest(file=path.name, template=title):
                    self.assertIn("**Use when:**", section)
                    self.assertIn("**Fixed requirements:**", section)
                    self.assertIn("**Creative latitude:**", section)
                    self.assertIn("**Visual QA:**", section)
                    self.assertIn("**Evidence/status:**", section)
                    self.assertIn("```text", section)
        self.assertGreaterEqual(template_count, 23)

    def test_original_recipe_inventory_survives_asset_migration(self):
        expected = {
            "generation-core.md": {
                "Editorial or article illustration",
                "Transparent asset, icon, or sprite",
            },
            "editing-core.md": {
                "Replace or remove one object",
                "Replace or localize text",
                "Identity-preserving composite",
                "Product placement or multi-reference composition",
                "Lighting, weather, or time-of-day change",
                "Sketch or layout to finished rendering",
                "Outpaint or change aspect ratio",
                "Consolidated drift-reset edit",
            },
            "layout-and-text.md": {
                "Exact-text poster or social card",
                "Technical or educational infographic",
                "UI concept image",
            },
            "characters-and-series.md": {"Character consistency sheet"},
            "brand-product-and-space.md": {"Product hero"},
        }
        for filename, titles in expected.items():
            text = (TEMPLATE_DIR / filename).read_text(encoding="utf-8")
            actual = set(re.findall(r"(?m)^## (.+)$", text))
            with self.subTest(filename=filename):
                self.assertTrue(titles.issubset(actual), titles - actual)

    def test_published_skill_does_not_reference_system_imagegen(self):
        published = []
        paths = [
            SKILL_DIR / "SKILL.md",
            *(SKILL_DIR / "references").rglob("*.md"),
            *(SKILL_DIR / "assets").rglob("*.md"),
            SKILL_DIR / "scripts" / "gpt_image_api.py",
        ]
        for path in paths:
            published.append(path.read_text(encoding="utf-8"))
        text = "\n".join(published).lower()
        visible_text = re.sub(r"https?://[^\s)]+", "", text)
        self.assertNotIn("$imagegen", text)
        self.assertNotIn("system imagegen", text)
        self.assertNotIn("built-in image_gen", text)
        self.assertNotIn("openrouter", text)
        self.assertIsNone(re.search(r"gpt-image-2(?![.-]5)", visible_text))

    def test_cli_and_eval_contract_are_present(self):
        self.assertTrue((SKILL_DIR / "scripts" / "gpt_image_api.py").is_file())
        evals = json.loads((SKILL_DIR / "evals" / "evals.json").read_text())
        self.assertEqual(evals["skill_name"], "gpt-image-api")
        self.assertGreaterEqual(len(evals["evals"]), 9)
        self.assertIn(
            "complete-specialized-brief-bypasses-templates",
            {item["name"] for item in evals["evals"]},
        )

    def test_live_eval_plan_and_generation_matrix_are_reproducible(self):
        plan = (SKILL_DIR / "evals" / "live-eval-plan.md").read_text(
            encoding="utf-8"
        )
        matrix_lines = [
            line
            for line in (SKILL_DIR / "evals" / "live" / "generation-matrix.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertIn("Generation matrix", plan)
        self.assertIn("Edit matrix", plan)
        self.assertIn("Scoring rubric", plan)
        self.assertEqual(len(matrix_lines), 16)
        models = {json.loads(line)["model"] for line in matrix_lines}
        self.assertEqual(models, {"flare", "sunburst"})
        self.assertTrue((SKILL_DIR / "evals" / "live" / "scorecard-template.md").is_file())

    def test_catalogs_publish_new_name_and_remove_old_skill_name(self):
        for relative in (
            "docs/skills-catalog.en.md",
            "docs/skills-catalog.zh-CN.md",
        ):
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn("gpt-image-api", text)
                self.assertNotIn("--skill gpt-image-2`", text)

    def test_legacy_skill_is_archived_outside_published_skills(self):
        self.assertFalse((REPO_ROOT / "skills" / "gpt-image-2").exists())
        archived = REPO_ROOT / "archive" / "skills" / "gpt-image-2"
        self.assertTrue((archived / "SKILL.md").is_file())
        self.assertTrue((archived / "ARCHIVED.md").is_file())


if __name__ == "__main__":
    unittest.main()
