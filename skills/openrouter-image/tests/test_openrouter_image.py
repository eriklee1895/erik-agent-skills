from __future__ import annotations

import base64
import http.client
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
        self.assertEqual([(entry["name"], entry["status"]) for entry in summary],
                         [(f"poster-{i}", "ok") for i in range(3)])

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
            "output_compression": [-1, 101, "80", 1.5, True, [], {}],
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
            {"prompt": "Bad compression", "output_compression": 101},
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
        self.write_jobs([{"name": "poster", "prompt": "Poster"}])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(mod.run_batch(self.input, self.out, 123), 1)
        entry = json.loads((self.out / "batch-summary.json").read_text())[0]
        self.assertEqual(entry["name"], "poster")
        self.assertEqual(entry["status"], "HTTP 429: slow down")
        self.assertIsNone(entry["cost"])
        self.assertEqual(entry["outputs"], [])


class RequestTests(OfflineTests):
    def test_output_compression_bounds_match_model_matrix(self):
        for model in ("sunburst", "flare"):
            for value in (0, 100):
                with self.subTest(model=model, compression=value):
                    self.assertEqual(self.request(model_name=model, compression=value)[
                        "output_compression"], value)
            for value in (-1, 101):
                with self.subTest(model=model, compression=value):
                    with self.assertRaisesRegex(SystemExit, "output_compression.*0.*100"):
                        self.request(model_name=model, compression=value)

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


class BatchReliabilityTests(OfflineTests):
    def execute_batch(self, jobs):
        self.write_jobs(jobs)
        with redirect_stdout(io.StringIO()):
            code = mod.run_batch(self.input, self.out, 123)
        return code, json.loads((self.out / "batch-summary.json").read_text())

    def test_colliding_output_names_fail_before_any_api_calls(self):
        cases = (
            [{"name": "poster"}, {"name": "poster"}],
            [{"name": "Poster"}, {"name": "poster"}],
            [{"name": "poster", "n": 2}, {"name": "poster-1"}],
            [{"name": "poster", "n": 2}, {"name": "poster"}],
            [{"name": "batch-summary"}],
        )
        for rows in cases:
            with self.subTest(rows=rows):
                self.write_jobs([{"prompt": "Poster", **row} for row in rows])
                with self.assertRaisesRegex(SystemExit, r"batch line \d+: .*collision"):
                    mod.run_batch(self.input, self.out, 123)
                self.api.assert_not_called()
                self.assertFalse(self.out.exists())

    def test_batch_names_cannot_write_outside_output_directory(self):
        for name in ("../escape", str(self.root / "escape"), "nested/poster", "nested\\poster", ".", "..", "bad\x00name"):
            with self.subTest(name=name):
                self.write_jobs([{"prompt": "Poster", "name": name}])
                with self.assertRaisesRegex(SystemExit, "batch line 1: .*name"):
                    mod.run_batch(self.input, self.out, 123)
                self.api.assert_not_called()
                self.assertFalse(self.out.exists())

    def test_existing_directory_at_later_output_aborts_before_api(self):
        (self.out / "second.png").mkdir(parents=True)
        self.write_jobs([{"name": name, "prompt": "Poster"} for name in ("first", "second")])
        with self.assertRaisesRegex(SystemExit, "batch line 2: .*output"):
            mod.run_batch(self.input, self.out, 123)
        self.api.assert_not_called()
        self.assertFalse((self.out / "first.png").exists())

    def test_variant_dry_runs_list_numbered_output_paths(self):
        self.write_jobs([{"name": "poster", "prompt": "Poster", "n": 2}])
        batch = json.loads(self.run_cli("batch", "--input", str(self.input),
                                       "--out-dir", str(self.out), "--dry-run"))
        single = json.loads(self.run_cli("generate", "--prompt", "Poster", "--n", "2",
                                        "--out", str(self.out / "poster.png"), "--dry-run"))
        expected = [str(self.out / "poster-1.png"), str(self.out / "poster-2.png")]
        self.assertEqual(batch["jobs"][0]["outputs"], expected)
        self.assertEqual(single["outputs"], expected)
        self.api.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_success_summary_records_cost_model_line_and_actual_outputs(self):
        self.api.return_value["data"] *= 2
        code, summary = self.execute_batch([{"name": "poster", "prompt": "Poster", "n": 2}])
        self.assertEqual(code, 0)
        self.assertEqual(summary[0]["status"], "ok")
        self.assertEqual(summary[0]["line"], 1)
        self.assertEqual(summary[0]["model"], mod.MODELS["sunburst"]["id"])
        self.assertEqual(summary[0]["cost"], 0.01)
        self.assertEqual(summary[0]["outputs"], [str(self.out / "poster-1.png"),
                                                  str(self.out / "poster-2.png")])
        self.assertGreaterEqual(summary[0]["elapsed_seconds"], 0)
        self.assertTrue(all(Path(p).read_bytes() == b"image bytes" for p in summary[0]["outputs"]))

    def test_network_failure_is_recorded_without_retry_and_later_jobs_continue(self):
        response = self.api.return_value
        self.api.side_effect = [response, urllib.error.URLError("connection reset"), response]
        code, summary = self.execute_batch([{"name": name, "prompt": name}
                                            for name in ("first", "failed", "last")])
        self.assertEqual(code, 1)
        self.assertEqual(self.api.call_count, 3)
        self.assertEqual([entry["status"] for entry in summary][::2], ["ok", "ok"])
        self.assertIn("connection reset", summary[1]["status"])
        self.assertIsNone(summary[1]["cost"])
        self.assertEqual(summary[1]["outputs"], [])
        self.assertTrue((self.out / "first.json").exists())
        self.assertTrue((self.out / "last.png").exists())

    def test_completed_jobs_are_checkpointed_before_the_next_request(self):
        response = self.api.return_value
        def next_call(body, timeout):
            if body["prompt"] == "second":
                checkpoint = json.loads((self.out / "batch-summary.json").read_text())
                self.assertEqual(len(checkpoint), 1)
                self.assertEqual(checkpoint[0]["name"], "first")
                self.assertEqual(checkpoint[0]["cost"], 0.01)
            return response
        self.api.side_effect = next_call
        self.execute_batch([{"name": name, "prompt": name} for name in ("first", "second")])

    def test_interrupt_preserves_completed_job_summary(self):
        self.api.side_effect = [self.api.return_value, KeyboardInterrupt()]
        self.write_jobs([{"name": name, "prompt": name} for name in ("first", "second")])
        with redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
            mod.run_batch(self.input, self.out, 123)
        summary = json.loads((self.out / "batch-summary.json").read_text())
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["name"], "first")
        self.assertEqual(summary[0]["status"], "ok")

    def test_batch_cli_exits_nonzero_for_failed_jobs(self):
        self.api.side_effect = TimeoutError("timed out")
        self.write_jobs([{"name": "poster", "prompt": "Poster"}])
        with self.assertRaises(SystemExit) as error:
            self.run_cli("batch", "--input", str(self.input), "--out-dir", str(self.out))
        self.assertEqual(error.exception.code, 1)
        self.assertEqual(self.api.call_count, 1)
        entry = json.loads((self.out / "batch-summary.json").read_text())[0]
        self.assertIn("timed out", entry["status"])
        self.assertIsNone(entry["cost"])

    def test_metadata_failure_preserves_saved_paths_and_reported_cost(self):
        with mock.patch.object(mod, "write_meta", side_effect=OSError("disk full")):
            code, summary = self.execute_batch([{"name": "poster", "prompt": "Poster"}])
        self.assertEqual(code, 1)
        self.assertIn("disk full", summary[0]["status"])
        self.assertEqual(summary[0]["cost"], 0.01)
        self.assertEqual(summary[0]["outputs"], [str(self.out / "poster.png")])
        self.assertTrue((self.out / "poster.png").exists())

    def test_local_save_failure_stops_before_remaining_paid_calls(self):
        with mock.patch.object(mod, "write_meta", side_effect=OSError("disk full")):
            code, summary = self.execute_batch([{"name": name, "prompt": name}
                                                for name in ("first", "second")])
        self.assertEqual(code, 1)
        self.api.assert_called_once()
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["name"], "first")

    def test_one_returned_variant_uses_reserved_unnumbered_path(self):
        code, summary = self.execute_batch([{"name": "poster", "prompt": "Poster", "n": 2}])
        self.assertEqual(code, 0)
        self.assertEqual(summary[0]["outputs"], [str(self.out / "poster.png")])
        self.assertEqual((self.out / "poster.png").read_bytes(), b"image bytes")


class ImageSavingTests(OfflineTests):
    def test_malformed_responses_do_not_save_partial_or_empty_images(self):
        valid = self.api.return_value["data"][0]
        cases = (None, [], {"data": None}, {"data": {}}, {"data": [None]},
                 {"data": [valid, {}]}, {"data": [valid, {"b64_json": "!!!"}]},
                 {"data": [{"b64_json": 123}]}, {"data": [{"b64_json": "é"}]})
        for response in cases:
            with self.subTest(response=response):
                self.api.return_value = response
                self.write_jobs([{"name": "poster", "prompt": "Poster"}])
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(mod.run_batch(self.input, self.out, 123), 1)
                self.assertEqual(list(self.out.glob("*.png")), [])
                entry = json.loads((self.out / "batch-summary.json").read_text())[0]
                self.assertEqual(entry["outputs"], [])
                self.assertNotEqual(entry["status"], "ok")

    def test_single_cli_reports_network_and_json_errors_without_retry(self):
        errors = (urllib.error.URLError("connection reset"), TimeoutError("timed out"),
                  http.client.IncompleteRead(b"prefix", 5), ConnectionResetError("connection reset"),
                  json.JSONDecodeError("bad JSON", "x", 0))
        for error in errors:
            with self.subTest(error=error):
                self.api.reset_mock()
                self.api.side_effect = error
                with self.assertRaises(SystemExit) as caught:
                    self.run_cli("generate", "--prompt", "Poster", "--out", str(self.out / "poster.png"))
                self.assertNotEqual(caught.exception.code, 0)
                self.api.assert_called_once()
                self.assertFalse((self.out / "poster.png").exists())

    def test_image_target_cannot_overwrite_its_metadata(self):
        for n in (1, 2):
            with self.subTest(n=n), self.assertRaisesRegex(SystemExit, "metadata"):
                self.run_cli("generate", "--prompt", "Poster", "--n", str(n),
                             "--out", str(self.out / "poster.json"))
            self.api.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_ratio_remains_best_effort_without_pixel_validation(self):
        # The API boundary is mocked; no image codec or dimension checker is needed.
        self.run_cli("generate", "--prompt", "Poster", "--aspect", "3:4",
                     "--out", str(self.out / "poster.png"))
        self.assertEqual(self.api.call_args.args[0]["aspect_ratio"], "3:4")
        self.assertEqual((self.out / "poster.png").read_bytes(), b"image bytes")

    def test_partial_disk_failure_reports_completed_paths_and_cost(self):
        self.api.return_value["data"] *= 2
        original = mod.write_bytes_atomic
        def fail_second(path, data):
            if path.name == "poster-2.png":
                raise OSError("disk full")
            original(path, data)
        with mock.patch.object(mod, "write_bytes_atomic", side_effect=fail_second):
            result = mod.execute_request(self.request(n=2), self.out / "poster.png", 123)
        self.assertEqual(result["error_type"], "output")
        self.assertEqual(result["cost"], 0.01)
        self.assertEqual(result["outputs"], [str(self.out / "poster-1.png")])
        self.assertFalse((self.out / "poster-2.png").exists())

    def test_output_directory_creation_failure_prevents_paid_call(self):
        with mock.patch.object(Path, "mkdir", side_effect=PermissionError("read only directory")):
            with self.assertRaisesRegex(SystemExit, "read only directory"):
                self.run_cli("generate", "--prompt", "Poster", "--out", str(self.out / "poster.png"))
        self.api.assert_not_called()


if __name__ == "__main__":
    unittest.main()
