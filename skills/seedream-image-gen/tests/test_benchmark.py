"""The evaluation runner must preserve evidence and never replay a journaled case."""

import asyncio
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "evals" / "benchmark.py"
SPEC = importlib.util.spec_from_file_location("seedream_benchmark_runner", SCRIPT)
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


class BenchmarkEvidenceTests(unittest.TestCase):
    def test_comprehensive_suite_is_balanced_repeated_and_immutable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = benchmark.prepare(root, suite="comprehensive")
            cases = manifest["cases"]
            self.assertEqual(len(cases), 80)
            self.assertEqual(len({case["id"] for case in cases}), 80)
            self.assertEqual(len({case["case"] for case in cases}), 18)
            for name in {case["case"] for case in cases}:
                selected = [case for case in cases if case["case"] == name]
                for model in ("pro", "flash"):
                    pair = [case for case in selected if case["model"] == model and case["mode"] == "standard"]
                    self.assertEqual(sorted(case["repeat"] for case in pair), [1, 2])
                    self.assertEqual(len({case["prompt"] for case in pair}), 1)
                self.assertTrue(all(case["criteria"] for case in selected))
            self.assertEqual(sum(case["mode"] == "fast" for case in cases), 8)
            self.assertFalse((root / "cases").exists())
            fixture = root / "fixtures/objects.png"
            stamp = fixture.stat().st_mtime_ns
            self.assertEqual(benchmark.prepare(root, suite="comprehensive"), manifest)
            self.assertEqual(fixture.stat().st_mtime_ns, stamp)

    def test_generated_output_inspection_excludes_marker_previews(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            Image.new("RGB", (32, 32)).save(root / "sample.png")
            Image.new("RGB", (32, 32)).save(root / "sample-annotated.png")
            self.assertEqual([output["file"] for output in benchmark.inspect_outputs(root)], ["sample.png"])

    def test_case_arguments_keep_marker_and_output_settings(self):
        case = dict(command="edit", model="pro", prompt="change the marked title", size="1.5K",
                    mode="standard", references=["objects.png"], output_format="jpeg",
                    marker_rect=["10%,10%,30%,20%"], marker_color=["#ff0000"])
        args = benchmark.case_arguments(Path("/study"), case, Path("/study/cases/sample"))
        self.assertIn("--marker-rect", args)
        self.assertIn("10%,10%,30%,20%", args)
        self.assertEqual(args[args.index("--output-format") + 1], "jpeg")
        self.assertIn("--no-negative-prompt", args)

    def test_preparing_existing_study_does_not_rewrite_its_fixtures(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = benchmark.prepare(root)
            fixture = root / "fixtures/objects.png"
            stamp = fixture.stat().st_mtime_ns
            second = benchmark.prepare(root)
            self.assertEqual(first, second)
            self.assertEqual(fixture.stat().st_mtime_ns, stamp)

    def test_modified_reference_is_rejected_without_destroying_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            benchmark.prepare(root)
            fixture = root / "fixtures/objects.png"
            fixture.write_bytes(b"preserve modified local evidence")
            with self.assertRaises(SystemExit):
                benchmark.prepare(root)
            self.assertEqual(fixture.read_bytes(), b"preserve modified local evidence")

    def test_existing_submitted_case_is_never_executed_again(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            journal = root / "cases/sample/result.json"
            journal.parent.mkdir(parents=True)
            original = '{"status":"submitted","generation_attempts":1}'
            journal.write_text(original)
            with patch.object(benchmark.asyncio, "create_subprocess_exec", new=AsyncMock(
                side_effect=AssertionError("A journaled paid request must not run again")
            )):
                asyncio.run(benchmark.execute(root, [{"id": "sample"}], concurrency=2))
            self.assertEqual(json.loads(journal.read_text()), json.loads(original))


if __name__ == "__main__":
    unittest.main()
