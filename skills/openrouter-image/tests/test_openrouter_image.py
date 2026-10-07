from __future__ import annotations

import base64
import importlib.util
import io
import json
import os
import re
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "openrouter_image.py"
spec = importlib.util.spec_from_file_location("openrouter_image", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class OfflineTests(unittest.TestCase):
    def setUp(self):
        tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(tmp)
        self.input = self.root / "jobs.jsonl"
        self.out = self.root / "out"
        self.api = self.enterContext(mock.patch.object(mod, "call_api", return_value={
            "data": [{"b64_json": base64.b64encode(b"image bytes").decode()}],
            "usage": {"cost": 0.01},
        }))
        self.enterContext(mock.patch.object(mod, "load_env"))
        self.enterContext(mock.patch.dict(os.environ, {}, clear=True))
        self.enterContext(mock.patch.object(
            mod.urllib.request, "urlopen", side_effect=AssertionError("network forbidden")))

    def write_jobs(self, jobs):
        self.input.write_text("\n".join(json.dumps(job) for job in jobs), encoding="utf-8")

    def run_batch(self, jobs):
        self.write_jobs(jobs)
        with redirect_stdout(io.StringIO()):
            mod.run_batch(self.input, self.out, 123)
        return [call.args[0] for call in self.api.call_args_list]

    def run_cli(self, *args):
        stdout = io.StringIO()
        with mock.patch("sys.argv", [str(SCRIPT_PATH), *args]), redirect_stdout(stdout):
            mod.main()
        return stdout.getvalue()

    def request(self, **overrides):
        args = dict(model_name="sunburst", prompt="A poster", aspect="1:1",
                    quality=None, resolution=None, background=None, n=1,
                    refs=[], compression=None)
        args.update(overrides)
        return mod.build_request(**args)


class BatchTests(OfflineTests):
    def test_documented_jsonl_examples_preserve_non_square_ratios(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        blocks = re.findall(r"```json\n(.*?)\n```", text, re.S)
        jobs = [json.loads(line) for block in blocks for line in block.splitlines()]
        self.assertEqual(len(jobs), 2)
        bodies = self.run_batch(jobs)
        self.assertEqual([body["aspect_ratio"] for body in bodies], ["3:4", "21:9"])
        self.assertEqual(bodies[0]["quality"], "high")
        self.assertEqual(bodies[1]["resolution"], "4K")
        for job in jobs:
            self.assertIn("aspect_ratio", job)
            self.assertNotIn("aspect", job)

    def test_canonical_legacy_and_equal_dual_aspect_keys(self):
        jobs = [dict(name=f"poster-{i}", prompt="A poster", **aspect)
                for i, aspect in enumerate((
                    {"aspect_ratio": "3:4"},
                    {"aspect": "3:4"},
                    {"aspect_ratio": "3:4", "aspect": "3:4"},
                ))]
        bodies = self.run_batch(jobs)
        self.assertEqual([body["aspect_ratio"] for body in bodies], ["3:4"] * 3)
        self.assertTrue(all("aspect" not in body for body in bodies))
        self.assertEqual((self.out / "poster-1.png").read_bytes(), b"image bytes")
        metadata = json.loads((self.out / "poster-1.json").read_text())
        self.assertEqual(metadata["request"]["aspect_ratio"], "3:4")
        self.assertEqual(metadata["usage"]["cost"], 0.01)
        summary = json.loads((self.out / "batch-summary.json").read_text())
        self.assertEqual(summary, [{"name": f"poster-{i}", "status": "ok"}
                                   for i in range(3)])

    def test_conflicting_aspect_keys_fail_before_api(self):
        self.write_jobs([{"prompt": "A poster", "aspect_ratio": "3:4", "aspect": "21:9"}])
        with self.assertRaisesRegex(SystemExit, r"batch line 1: .*conflict.*aspect"):
            mod.run_batch(self.input, self.out, 123)
        self.api.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_defaults_apply_when_fields_are_omitted(self):
        bodies = self.run_batch([{"prompt": "Poster"}, {"model": "banana", "prompt": "Lake"}])
        self.assertEqual(bodies, [
            {"model": mod.MODELS["sunburst"]["id"], "prompt": "Poster",
             "aspect_ratio": "1:1", "n": 1, "quality": "auto"},
            {"model": mod.MODELS["banana"]["id"], "prompt": "Lake",
             "aspect_ratio": "1:1", "n": 1, "resolution": "1K"},
        ])
        self.assertTrue((self.out / "job-000.png").is_file())
        self.assertTrue((self.out / "job-001.png").is_file())

    def test_explicit_nulls_are_rejected_for_every_supported_field(self):
        for field in ("model", "prompt", "name", "aspect", "aspect_ratio", "quality",
                      "resolution", "background", "n", "images", "output_compression"):
            with self.subTest(field=field):
                self.write_jobs([{"prompt": "Poster", field: None}])
                with self.assertRaisesRegex(SystemExit, rf"batch line 1: .*{field}"):
                    mod.run_batch(self.input, self.out, 123)
                self.api.assert_not_called()
                self.assertFalse(self.out.exists())

    def test_invalid_values_and_types_have_line_errors(self):
        cases = {
            "model": ["", "unknown", [], {}],
            "prompt": ["", "  ", 12, [], {}],
            "name": ["", "  ", 12, [], {}],
            "aspect_ratio": ["", "7:3", 1, [], {}],
            "aspect": ["", "7:3", 1, [], {}],
            "quality": ["", "ultra", 1, [], {}],
            "background": ["", "glass", True, [], {}],
            "n": [0, 11, 1.5, "1", True, [], {}],
            "images": ["reference.png", 1, {}, [1], [""], [False]],
            "output_compression": ["80", 1.5, True, [], {}],
        }
        for field, values in cases.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.write_jobs([{"prompt": "Poster", field: value}])
                    with self.assertRaisesRegex(SystemExit, rf"batch line 1: .*{field}"):
                        mod.run_batch(self.input, self.out, 123)
                    self.api.assert_not_called()
                    self.assertFalse(self.out.exists())
        for value in ("", "8K", 512, [], {}):
            with self.subTest(resolution=value):
                self.write_jobs([{"model": "banana", "prompt": "Lake", "resolution": value}])
                with self.assertRaisesRegex(SystemExit, r"batch line 1: .*resolution"):
                    mod.run_batch(self.input, self.out, 123)
                self.api.assert_not_called()

    def test_unknown_fields_fail_with_field_name_and_line_number(self):
        self.write_jobs([{"prompt": "Poster", "aspect_ration": "3:4"}])
        with self.assertRaisesRegex(SystemExit, r"batch line 1: .*unknown.*aspect_ration"):
            mod.run_batch(self.input, self.out, 123)
        self.api.assert_not_called()

    def test_invalid_later_row_prevents_all_api_calls(self):
        invalid_rows = (
            {"prompt": "Bad ratio", "aspect_ratio": "7:3"},
            {"prompt": "Bad quality", "quality": "ultra"},
            {"prompt": "Conflict", "aspect_ratio": "3:4", "aspect": "21:9"},
            {"prompt": "Missing ref", "images": [str(self.root / "missing.png")]},
            {"prompt": "Bad ref format", "images": [str(self.root / "ref.gif")]},
            {"prompt": "Bad field", "quailty": "high"},
            {"model": "banana", "prompt": "Dialect mismatch", "quality": "high"},
            {},
            [],
            "not an object",
            None,
        )
        for row in invalid_rows:
            with self.subTest(row=row):
                self.input.write_text("# jobs\n\n" + json.dumps({"prompt": "Valid"}) +
                                      "\n" + json.dumps(row), encoding="utf-8")
                with self.assertRaisesRegex(SystemExit, r"batch line 4:"):
                    mod.run_batch(self.input, self.out, 123)
                self.api.assert_not_called()
                self.assertFalse(self.out.exists())

    def test_invalid_json_has_physical_line_number(self):
        self.input.write_text('# jobs\n\n{"prompt":"Valid"}\n{"prompt":', encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, r"batch line 4: .*JSON"):
            mod.run_batch(self.input, self.out, 123)
        self.api.assert_not_called()

    def test_batch_dry_run_prints_normalized_requests_and_writes_nothing(self):
        reference = self.root / "ref.png"
        reference.write_bytes(b"reference bytes")
        self.write_jobs([
            {"name": "poster", "prompt": "Poster", "aspect": "3:4", "images": [str(reference)]},
            {"name": "wide", "model": "banana", "prompt": "Lake", "aspect_ratio": "21:9",
             "resolution": "4K"},
        ])
        preview = json.loads(self.run_cli("batch", "--input", str(self.input),
                                         "--out-dir", str(self.out), "--dry-run"))
        self.assertEqual(len(preview["jobs"]), 2)
        self.assertEqual(preview["jobs"][0]["line"], 1)
        self.assertEqual(preview["jobs"][0]["name"], "poster")
        self.assertEqual(preview["jobs"][0]["model_alias"], "sunburst")
        self.assertEqual(preview["jobs"][0]["request"]["aspect_ratio"], "3:4")
        self.assertEqual(preview["jobs"][0]["outputs"], [str(self.out / "poster.png")])
        self.assertEqual(preview["jobs"][1]["request"]["resolution"], "4K")
        ref_url = preview["jobs"][0]["request"]["input_references"][0]["image_url"]["url"]
        self.assertEqual(base64.b64decode(ref_url.split(",")[1]), b"reference bytes")
        self.api.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_batch_dry_run_validates_later_rows(self):
        self.write_jobs([{"prompt": "Valid"}, {"prompt": "Bad", "quality": "ultra"}])
        with self.assertRaisesRegex(SystemExit, r"batch line 2: .*quality"):
            self.run_cli("batch", "--input", str(self.input),
                         "--out-dir", str(self.out), "--dry-run")
        self.api.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_comments_and_blank_lines_keep_existing_default_output_names(self):
        self.input.write_text('# header\n\n{"prompt":"Poster"}\n', encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            mod.run_batch(self.input, self.out, 123)
        self.assertTrue((self.out / "job-002.png").is_file())

    def test_http_failure_still_writes_batch_summary(self):
        self.api.side_effect = urllib.error.HTTPError(
            mod.API_URL, 429, "rate limited", {}, io.BytesIO(b"slow down"))
        self.run_batch([{"name": "poster", "prompt": "Poster"}])
        self.assertEqual(json.loads((self.out / "batch-summary.json").read_text()),
                         [{"name": "poster", "status": "HTTP 429: slow down"}])


class RequestTests(OfflineTests):
    def test_all_model_matrix_quality_and_resolution_values_are_accepted(self):
        for model in ("sunburst", "flare"):
            for quality in ("auto", "low", "medium", "high", "xhigh", "max"):
                with self.subTest(model=model, quality=quality):
                    body = self.request(model_name=model, quality=quality)
                    self.assertEqual(body["quality"], quality)
        for resolution in ("512", "1K", "2K", "4K"):
            with self.subTest(resolution=resolution):
                body = self.request(model_name="banana", resolution=resolution)
                self.assertEqual(body["resolution"], resolution)

    def test_shared_builder_rejects_invalid_quality_and_resolution(self):
        for model, field in (("sunburst", "quality"), ("flare", "quality"),
                             ("banana", "resolution")):
            for value in ("", "invalid", 1, [], {}):
                with self.subTest(model=model, field=field, value=value):
                    with self.assertRaisesRegex(SystemExit, field):
                        self.request(model_name=model, **{field: value})

    def test_shared_builder_rejects_non_integer_variant_count(self):
        for value in (None, "1", 1.0, True, [], {}):
            with self.subTest(n=value), self.assertRaisesRegex(SystemExit, "n must"):
                self.request(n=value)

    def test_model_limits_and_dialect_checks_remain_in_effect(self):
        for kwargs in ({"n": 11}, {"model_name": "banana", "n": 2},
                       {"refs": [Path("ref.png")] * 17},
                       {"model_name": "banana", "refs": [Path("ref.png")] * 15},
                       {"model_name": "banana", "aspect": "auto"},
                       {"resolution": "1K"}, {"model_name": "banana", "quality": "high"},
                       {"model_name": "banana", "background": "transparent"},
                       {"model_name": "banana", "compression": 80}):
            with self.subTest(kwargs=kwargs), self.assertRaises(SystemExit):
                self.request(**kwargs)

    def test_generate_dry_run_preserves_aspect_prompt_and_gpt_options(self):
        prompt = "  保持文字与空格  "
        preview = json.loads(self.run_cli(
            "generate", "--model", mod.MODELS["flare"]["id"], "--prompt", prompt,
            "--aspect", "3:4", "--quality", "xhigh", "--n", "2",
            "--background", "transparent", "--output-compression", "80",
            "--out", str(self.out / "poster.png"), "--dry-run"))
        self.assertEqual(preview["model_alias"], "flare")
        self.assertEqual(preview["request"], {
            "model": mod.MODELS["flare"]["id"], "prompt": prompt,
            "aspect_ratio": "3:4", "quality": "xhigh", "n": 2,
            "background": "transparent", "output_compression": 80,
        })
        self.api.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_edit_dry_run_preserves_banana_resolution_and_reference(self):
        reference = self.root / "product.png"
        reference.write_bytes(b"reference bytes")
        prompt_file = self.root / "prompt.txt"
        prompt_file.write_text("Preserve product.\nChange background.", encoding="utf-8")
        preview = json.loads(self.run_cli(
            "edit", "--model", "banana", "--prompt-file", str(prompt_file),
            "--image", str(reference), "--aspect", "21:9", "--resolution", "4K",
            "--out", str(self.out / "edit.png"), "--dry-run"))
        self.assertEqual(preview["request"]["aspect_ratio"], "21:9")
        self.assertEqual(preview["request"]["resolution"], "4K")
        self.assertEqual(preview["request"]["prompt"], prompt_file.read_text())
        self.assertTrue(preview["request"]["input_references"][0]["image_url"]["url"].startswith(
            "data:image/png;base64,"))
        self.api.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_generate_and_edit_reject_bad_detail_values_before_api(self):
        for command in ("generate", "edit"):
            for model, field, value in (("sunburst", "quality", "ultra"),
                                        ("banana", "resolution", "8K")):
                with self.subTest(command=command, model=model):
                    with self.assertRaisesRegex(SystemExit, field):
                        self.run_cli(command, "--model", model, "--prompt", "Poster",
                                     f"--{field}", value, "--out", str(self.out / "bad.png"))
                    self.api.assert_not_called()


if __name__ == "__main__":
    unittest.main()
