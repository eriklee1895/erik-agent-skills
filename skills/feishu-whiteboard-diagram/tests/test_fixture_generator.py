import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GENERATOR = load_module(
    "feishu_fixture_generator",
    ROOT / "evals" / "generate_human_eval_fixtures.py",
)
LINTER = load_module("feishu_svg_linter", ROOT / "scripts" / "lint_svg.py")


class FixtureGeneratorTests(unittest.TestCase):
    def test_solid_box_declares_an_accessible_background_pair(self):
        parts: list[str] = []
        GENERATOR.solid_box(
            parts,
            0,
            0,
            320,
            120,
            GENERATOR.RISO_ORANGE,
            "判断",
            "谁决策",
        )
        fragment = "".join(parts)
        self.assertIn(f'data-bg="{GENERATOR.RISO_ORANGE}"', fragment)
        self.assertIn(f'fill="{GENERATOR.RISO_INK}"', fragment)

    def test_hub_spokes_are_explicitly_undirected(self):
        source = GENERATOR.hub_spoke()
        self.assertEqual(6, source.count('data-role="spoke"'))

    def test_directed_helpers_mark_edges(self):
        self.assertIn(
            'data-role="edge"',
            GENERATOR.line(0, 0, 100, 0, "#000000"),
        )
        self.assertIn(
            'data-role="edge"',
            GENERATOR.poly("0,0 100,0", "#000000"),
        )

    def test_primary_palette_text_pairs_meet_normal_text_contrast(self):
        pairs = [
            (GENERATOR.RISO_CREAM, GENERATOR.RISO_GREEN),
            (GENERATOR.RISO_INK, GENERATOR.RISO_ORANGE),
            (GENERATOR.CORAL_INK, GENERATOR.CORAL),
            ("#F4F1E6", GENERATOR.GROVE_TERRA),
            ("#FFFFFF", GENERATOR.RIPTIDE_COBALT),
            ("#FFFFFF", GENERATOR.AVO_BLUE),
        ]
        for foreground, background in pairs:
            with self.subTest(foreground=foreground, background=background):
                ratio = LINTER.contrast_ratio(foreground, background)
                self.assertIsNotNone(ratio)
                self.assertGreaterEqual(ratio, 4.5)

    def test_committed_fixtures_match_generator(self):
        fixture_dir = ROOT / "evals" / "fixtures" / "human-eval"
        expected = {
            "01-layered-strip.svg": GENERATOR.layered_strip(),
            "02-task-loop.svg": GENERATOR.task_loop(),
            "03-learning-loop.svg": GENERATOR.learning_loop(),
            "04-multicolumn-runtime.svg": GENERATOR.multicolumn_runtime(),
            "05-recovery-layers.svg": GENERATOR.recovery_layers(),
            "06-sequence.mmd": GENERATOR.MERMAID,
            "07-packet-flow.html": GENERATOR.HTML,
            "09-comparison.svg": GENERATOR.comparison_matrix(),
            "10-hub.svg": GENERATOR.hub_spoke(),
            "11-timeline.svg": GENERATOR.turn_timeline(),
            "12-swimlane.svg": GENERATOR.swimlane_handshake(),
            "13-quadrant.svg": GENERATOR.reuse_quadrant(),
            "14-focus-detail.svg": GENERATOR.focus_detail(),
            "eval-doc.xml": GENERATOR.EVAL_DOC,
        }
        for name, generated in expected.items():
            with self.subTest(name=name):
                committed = (fixture_dir / name).read_text(encoding="utf-8")
                self.assertEqual(generated, committed)


if __name__ == "__main__":
    unittest.main()
