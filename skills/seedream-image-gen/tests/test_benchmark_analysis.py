"""Scientific accounting: cost tiers, missing cases and public field selection."""

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "evals/analyze_benchmark.py"
SPEC = importlib.util.spec_from_file_location("seedream_benchmark_analysis", SCRIPT)
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


class BenchmarkAnalysisTests(unittest.TestCase):
    def test_layer_prices_use_each_crop_size_and_extra_pro_inputs(self):
        case = {
            "model": "pro",
            "command": "decompose",
            "references": ["a.png", "b.png"],
        }
        record = {
            "status": "success",
            "outputs": [{"size": [1536, 1536]}, {"size": [2048, 2048]}],
        }
        self.assertAlmostEqual(analysis.observed_cost(case, record), 0.47)
        case["model"] = "flash"
        self.assertAlmostEqual(analysis.observed_cost(case, record), 0.24)
        record["status"] = "outcome_unknown"
        self.assertIsNone(analysis.observed_cost(case, record))

    def test_summary_keeps_unknown_and_unrun_cases_in_denominator(self):
        rows = [
            {
                "status": "success",
                "generation_attempts": 1,
                "outputs": [{}],
                "list_cost_cny": 0.3,
            },
            {
                "status": "outcome_unknown",
                "generation_attempts": 1,
                "outputs": [],
                "list_cost_cny": None,
            },
            {
                "status": "not_run",
                "generation_attempts": 0,
                "outputs": [],
                "list_cost_cny": None,
            },
        ]
        summary = analysis.accounting(rows)
        self.assertEqual(summary["planned_requests"], 3)
        self.assertEqual(summary["submitted_requests"], 2)
        self.assertEqual(summary["successful_requests"], 1)
        self.assertEqual(summary["outputs"], 1)
        self.assertEqual(summary["statuses"]["outcome_unknown"], 1)
        self.assertTrue(summary["unknown_cost_present"])

    def test_request_export_omits_images_urls_and_credentials(self):
        request = {
            "model": "provider-id",
            "prompt": "fixture",
            "size": "1K",
            "background": "opaque",
            "image": "data:image/png;base64,private",
            "url": "https://signed.invalid/secret",
            "api_key": "private",
        }
        self.assertEqual(
            analysis.public_request(request),
            {
                "model": "provider-id",
                "prompt": "fixture",
                "size": "1K",
                "background": "opaque",
            },
        )


if __name__ == "__main__":
    unittest.main()
