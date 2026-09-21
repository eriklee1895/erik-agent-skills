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

    def test_model_selection_is_agent_owned_with_explicit_user_override(self):
        skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        model_text = (SKILL_DIR / "references" / "model-selection.md").read_text(
            encoding="utf-8"
        )
        for needle in (
            "agent chooses",
            "explicit model",
            "Do not run both models",
            "explicitly requests a comparison",
            "Pass the resolved model",
        ):
            with self.subTest(file="SKILL.md", needle=needle):
                self.assertIn(needle, skill_text)
        for needle in (
            "user explicitly names",
            "agent owns the default",
            "CLI default",
        ):
            with self.subTest(file="model-selection.md", needle=needle):
                self.assertIn(needle, model_text)

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
        scorecard = SKILL_DIR / "evals" / "live" / "scorecard-template.md"
        self.assertTrue(scorecard.is_file())
        regression = SKILL_DIR / "evals" / "live" / "regression-text-matrix.jsonl"
        regression_lines = [
            line
            for line in regression.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertIn("regression-text-matrix.jsonl", plan)
        self.assertEqual(len(regression_lines), 4)
        self.assertEqual(
            {json.loads(line)["model"] for line in regression_lines},
            {"flare", "sunburst"},
        )
        v3 = SKILL_DIR / "evals" / "live" / "regression-text-matrix-v3.jsonl"
        self.assertTrue(v3.is_file())
        v3_lines = [
            line for line in v3.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        self.assertEqual(len(v3_lines), 4)

    def test_live_findings_are_recorded_as_reusable_guidance(self):
        model_text = (SKILL_DIR / "references" / "model-selection.md").read_text(
            encoding="utf-8"
        )
        generation_text = (SKILL_DIR / "references" / "generation.md").read_text(
            encoding="utf-8"
        )
        layout_text = (
            SKILL_DIR / "assets" / "templates" / "layout-and-text.md"
        ).read_text(encoding="utf-8")
        community_text = (
            SKILL_DIR / "references" / "community-practices.md"
        ).read_text(encoding="utf-8")
        for needle in ("2026-09-16", "paired", "latency", "workflow"):
            with self.subTest(file="model-selection.md", needle=needle):
                self.assertIn(needle, model_text)
        for needle in ("allowlist", "unapproved", "critical", "Alpha"):
            with self.subTest(file="generation.md", needle=needle):
                self.assertIn(needle, generation_text)
        for needle in (
            "only",
            "unapproved",
            "critical failure",
            "deterministic",
            "missing",
        ):
            with self.subTest(file="layout-and-text.md", needle=needle):
                self.assertIn(needle, layout_text)
        for needle in ("27", "UI", "extra", "Sunburst", "omitted", "v3"):
            with self.subTest(file="community-practices.md", needle=needle):
                self.assertIn(needle, community_text)
        regression_report = (
            SKILL_DIR / "evals" / "live" / "results" / "2026-09-16-text-regression.md"
        )
        self.assertTrue(regression_report.is_file())
        report_text = regression_report.read_text(encoding="utf-8")
        for needle in ("v2", "v3", "omitted", "deterministic"):
            with self.subTest(file=regression_report.name, needle=needle):
                self.assertIn(needle, report_text)
        self.assertIn("Flare precision PASS / recall FAIL", report_text)
        self.assertIn("Sunburst precision PASS / recall PASS", report_text)
        self.assertIn(
            "UI: Flare omitted `VENDORS`, `SPECIALS`, and `PROFILE`", report_text
        )
        self.assertIn("UI: Sunburst omitted `PROFILE`", report_text)
        scorecard = (SKILL_DIR / "evals" / "live" / "scorecard-template.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Text precision", scorecard)
        self.assertIn("Text recall", scorecard)
        self.assertIn("PASS/FAIL/N/A", scorecard)
        self.assertIn("critical gate", scorecard)
        self.assertNotIn("product-hero | flare |  |  |  |  |  | PASS", scorecard)
        self.assertIn(
            "| transparent-sphere | flare |  |  |  |  |  |  | N/A |",
            scorecard,
        )
        plan_text = (SKILL_DIR / "evals" / "live-eval-plan.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Text precision", plan_text)
        self.assertIn("Identity/preservation", plan_text)
        self.assertNotIn("Text/identity/preservation", plan_text)
        self.assertIn("five numeric axes", plan_text)
        self.assertIn("UI: Flare omitted", community_text)
        self.assertIn("UI: Sunburst omitted", community_text)
        v3_prompt = (
            SKILL_DIR / "evals" / "live" / "regression-text-matrix-v3.jsonl"
        ).read_text(encoding="utf-8")
        self.assertNotIn("numbered nodes", v3_prompt)
        self.assertIn("ordered nodes", v3_prompt)
        self.assertIn("eval-run-20260916-01", report_text)

    def test_regression_evals_cover_observed_text_failures(self):
        evals = json.loads((SKILL_DIR / "evals" / "evals.json").read_text())
        names = {item["name"] for item in evals["evals"]}
        self.assertIn("strict-ui-text-allowlist", names)
        self.assertIn("strict-infographic-text-allowlist", names)
        self.assertIn("native-alpha-edge-qa", names)
        self.assertIn("workflow-specific-model-selection", names)
        self.assertIn("strict-ui-single-occurrence", names)
        self.assertIn("agent-owned-model-default", names)
        self.assertGreaterEqual(len(names), 15)

    def test_catalogs_publish_new_name_and_remove_old_skill_name(self):
        for relative in (
            "docs/skills-catalog.en.md",
            "docs/skills-catalog.zh-CN.md",
        ):
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(relative=relative):
                self.assertIn("gpt-image-api", text)
                self.assertIn("--skill gpt-image-2`", text)

    def test_previous_gpt_image_skill_remains_published(self):
        legacy = REPO_ROOT / "skills" / "gpt-image-2"
        self.assertTrue((legacy / "SKILL.md").is_file())
        self.assertTrue((legacy / "scripts" / "gpt_image_2.py").is_file())
        self.assertFalse((REPO_ROOT / "archive" / "skills" / "gpt-image-2").exists())


if __name__ == "__main__":
    unittest.main()
