"""The evaluation runner must preserve evidence and never replay a journaled case."""

import asyncio
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch


SCRIPT = Path(__file__).resolve().parents[1] / "evals" / "benchmark.py"
SPEC = importlib.util.spec_from_file_location("seedream_benchmark_runner", SCRIPT)
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


class BenchmarkEvidenceTests(unittest.TestCase):
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
