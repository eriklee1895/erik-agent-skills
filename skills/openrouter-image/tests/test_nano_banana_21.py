"""Offline CLI contract checks for the curated OpenRouter image models."""
import base64
import json
import importlib.util
import io
import urllib.error
from unittest.mock import patch
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "openrouter_image.py"
NEW_BANANA = "google/gemini-nano-banana-2.1"
PNG_BYTES = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6nAAAAABJRU5ErkJggg==")
JPEG_BYTES = base64.b64decode("/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDxyiiiv3E8w//Z")

WEBP_BYTES = base64.b64decode("UklGRjoAAABXRUJQVlA4IC4AAADQAQCdASoBAAEAAUAmJaACdLoB+AADsAD+82mX/mwIGaH0wf+mkeNI8aR8poAA")

def load_cli():
    spec = importlib.util.spec_from_file_location("image_cli", SCRIPT)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    return cli

class RequestContractTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "generate", "--prompt", "A blue ceramic cup", "--out", "/private/tmp/unused-image.png", "--dry-run", *args], text=True, capture_output=True)

    def request(self, *args):
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["request"]

    def test_banana_alias_uses_new_model_and_defaults_to_1k(self):
        body = self.request("--model", "banana")
        self.assertEqual(body["model"], NEW_BANANA)
        self.assertEqual(body["resolution"], "1K")
        self.assertNotIn("quality", body)

    def test_new_full_model_id_is_accepted(self):
        self.assertEqual(self.request("--model", NEW_BANANA)["model"], NEW_BANANA)

    def test_512_is_rejected_before_network(self):
        result = self.run_cli("--model", "banana", "--resolution", "512")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("1K, 2K, 4K", result.stderr)

    def test_invalid_resolution_is_rejected_before_network(self):
        for resolution in ("2k", "8K", "banana"):
            with self.subTest(resolution=resolution):
                self.assertNotEqual(self.run_cli("--model", "banana", "--resolution", resolution).returncode, 0)

    def test_banana_supported_tiers_and_ultrawide_ratio(self):
        for resolution in ("1K", "2K", "4K"):
            body = self.request("--model", "banana", "--resolution", resolution, "--aspect", "8:1")
            self.assertEqual(body["aspect_ratio"], "8:1")
            self.assertEqual(body["resolution"], resolution)

    def test_banana_rejects_gpt_controls_and_multiple_outputs(self):
        for flags in (("--quality", "high"), ("--background", "transparent"), ("--n", "2"), ("--aspect", "auto")):
            with self.subTest(flags=flags):
                self.assertNotEqual(self.run_cli("--model", "banana", *flags).returncode, 0)

    def test_reference_ceiling(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "ref.png"
            image.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6nAAAAABJRU5ErkJggg=="))
            flags = [flag for _ in range(14) for flag in ("--image", str(image))]
            self.assertEqual(len(self.request("--model", "banana", *flags)["input_references"]), 14)
            self.assertNotEqual(self.run_cli("--model", "banana", *flags, "--image", str(image)).returncode, 0)

    def test_reference_order_matches_repeated_image_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "person.png"
            second = Path(directory) / "product.png"
            first.write_bytes(JPEG_BYTES)
            second.write_bytes(PNG_BYTES)
            body = self.request("--model", "banana", "--image", str(first), "--image", str(second))
            encoded = [ref["image_url"]["url"].split(",", 1)[1] for ref in body["input_references"]]
            self.assertEqual([base64.b64decode(value) for value in encoded], [first.read_bytes(), second.read_bytes()])

    def test_batch_keeps_failure_summary_when_first_api_request_fails(self):
        spec = importlib.util.spec_from_file_location("image_cli", SCRIPT)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as directory:
            jobs = Path(directory) / "jobs.jsonl"
            jobs.write_text(json.dumps({"name": "draft", "model": "banana", "prompt": "blue cup", "resolution": "1K"}) + "\n")
            out_dir = Path(directory) / "new-output-directory"
            error = urllib.error.HTTPError(cli.API_URL, 429, "quota", {}, io.BytesIO(b'{"error":{"message":"quota"}}'))
            with patch.object(cli, "call_api", side_effect=error):
                cli.run_batch(jobs, out_dir, 10)
            summary = json.loads((out_dir / "batch-summary.json").read_text())
            self.assertEqual(summary[0]["name"], "draft")
            self.assertIn("HTTP 429", summary[0]["status"])

    def test_batch_accepts_legacy_and_matching_canonical_aspect(self):
        spec = importlib.util.spec_from_file_location("image_cli", SCRIPT)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as directory:
            jobs = Path(directory) / "jobs.jsonl"
            rows = [
                {"name": "legacy", "model": "banana", "prompt": "wide scene", "aspect": "8:1"},
                {"name": "canonical", "model": "banana", "prompt": "wide scene", "aspect": "21:9", "aspect_ratio": "21:9"},
            ]
            jobs.write_text("".join(json.dumps(row) + "\n" for row in rows))
            out_dir = Path(directory) / "output"
            response = {"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode()}], "usage": {"cost": 0.01}}
            with patch.object(cli, "call_api", return_value=response):
                cli.run_batch(jobs, out_dir, 10)
            self.assertEqual(json.loads((out_dir / "legacy.json").read_text())["request"]["aspect_ratio"], "8:1")
            self.assertEqual(json.loads((out_dir / "canonical.json").read_text())["request"]["aspect_ratio"], "21:9")

    def test_batch_rejects_unsupported_controls_before_api_call(self):
        spec = importlib.util.spec_from_file_location("image_cli", SCRIPT)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as directory:
            jobs = Path(directory) / "jobs.jsonl"
            response = {"data": [{"b64_json": base64.b64encode(PNG_BYTES).decode()}]}
            for field, value in (("thinking", "high"), ("search", True)):
                with self.subTest(field=field):
                    jobs.write_text(json.dumps({"name": "draft", "model": "banana", "prompt": "cup", field: value}) + "\n")
                    with patch.object(cli, "call_api", return_value=response):
                        with self.assertRaisesRegex(SystemExit, "unknown.*" + field):
                            cli.run_batch(jobs, Path(directory) / "output", 10)

    def test_gpt_models_keep_quality_transparency_and_variants(self):
        for model in ("sunburst", "flare"):
            body = self.request("--model", model, "--quality", "max", "--background", "transparent", "--n", "3")
            self.assertEqual(body["quality"], "max")
            self.assertEqual(body["background"], "transparent")
            self.assertEqual(body["n"], 3)
            self.assertNotIn("resolution", body)

    def test_invalid_gpt_quality_is_rejected_before_network(self):
        self.assertNotEqual(self.run_cli("--model", "flare", "--quality", "ultra").returncode, 0)

class ImageFormatTests(unittest.TestCase):
    def test_jpeg_output_uses_jpeg_extension_without_transcoding(self):
        cli = load_cli()
        with tempfile.TemporaryDirectory() as directory:
            requested = Path(directory) / "banana.png"
            response = {"data": [{"b64_json": base64.b64encode(JPEG_BYTES).decode()}]}
            paths = cli.save_images(response, requested)
            self.assertEqual(paths, [requested.with_suffix(".jpg")])
            self.assertEqual(paths[0].read_bytes(), JPEG_BYTES)
            self.assertFalse(requested.exists())
            cli.write_meta(requested, {"model": NEW_BANANA}, response, 1.0, paths)
            self.assertEqual(json.loads(requested.with_suffix(".json").read_text())["outputs"], [str(paths[0])])

    def test_reference_mime_comes_from_bytes_even_when_extension_is_wrong(self):
        cli = load_cli()
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "old-banana.png"
            image.write_bytes(JPEG_BYTES)
            url = cli.data_url(image)
            self.assertTrue(url.startswith("data:image/jpeg;base64,"))
            self.assertEqual(base64.b64decode(url.split(",", 1)[1]), JPEG_BYTES)

    def test_png_output_stays_png_even_if_provider_reports_jpeg(self):
        cli = load_cli()
        with tempfile.TemporaryDirectory() as directory:
            requested = Path(directory) / "asset.jpg"
            response = {"data": [{"media_type": "image/jpeg", "b64_json": base64.b64encode(PNG_BYTES).decode()}]}
            paths = cli.save_images(response, requested)
            self.assertEqual(paths, [requested.with_suffix(".png")])
            self.assertEqual(paths[0].read_bytes(), PNG_BYTES)

    def test_webp_bytes_control_output_suffix_and_reference_mime(self):
        cli = load_cli()
        with tempfile.TemporaryDirectory() as directory:
            requested = Path(directory) / "asset.png"
            response = {"data": [{"b64_json": base64.b64encode(WEBP_BYTES).decode()}]}
            paths = cli.save_images(response, requested)
            self.assertEqual(paths, [requested.with_suffix(".webp")])
            self.assertTrue(cli.data_url(paths[0]).startswith("data:image/webp;base64,"))

    def test_variants_keep_numbering_with_actual_formats(self):
        cli = load_cli()
        with tempfile.TemporaryDirectory() as directory:
            requested = Path(directory) / "candidate.png"
            response = {"data": [{"b64_json": base64.b64encode(raw).decode()} for raw in (JPEG_BYTES, PNG_BYTES)]}
            paths = cli.save_images(response, requested)
            self.assertEqual([p.name for p in paths], ["candidate-1.jpg", "candidate-2.png"])
            self.assertEqual([p.read_bytes() for p in paths], [JPEG_BYTES, PNG_BYTES])

    def test_jpeg_batch_summary_records_actual_paths_and_cost(self):
        cli = load_cli()
        with tempfile.TemporaryDirectory() as directory:
            jobs = Path(directory) / "jobs.jsonl"
            jobs.write_text(json.dumps({"name": "product", "model": "banana", "prompt": "blue bottle"}) + "\n")
            out = Path(directory) / "output"
            response = {"data": [{"b64_json": base64.b64encode(JPEG_BYTES).decode()}], "usage": {"cost": 0.035}}
            with patch.object(cli, "call_api", return_value=response):
                self.assertEqual(cli.run_batch(jobs, out, 10), 0)
            result = json.loads((out / "batch-summary.json").read_text())[0]
            self.assertEqual(result["outputs"], [str(out / "product.jpg")])
            self.assertEqual(result["cost"], 0.035)
            self.assertEqual(json.loads((out / "product.json").read_text())["outputs"], result["outputs"])

    def test_actual_encoding_targets_are_reserved_before_paid_calls(self):
        cli = load_cli()
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "output"
            out.mkdir()
            (out / "product.jpg").mkdir()
            jobs = Path(directory) / "jobs.jsonl"
            jobs.write_text(json.dumps({"name": "product", "model": "banana", "prompt": "blue bottle"}) + "\n")
            with patch.object(cli, "call_api", side_effect=AssertionError("network forbidden")):
                with self.assertRaisesRegex(SystemExit, "output target is not a file"):
                    cli.run_batch(jobs, out, 10)
            self.assertFalse((out / "batch-summary.json").exists())

    def test_unknown_raster_reports_generation_error_and_retains_known_cost(self):
        cli = load_cli()
        with tempfile.TemporaryDirectory() as directory:
            response = {"data": [{"b64_json": base64.b64encode(b"not an image").decode()}], "usage": {"cost": 0.035}}
            with patch.object(cli, "call_api", return_value=response):
                result = cli.execute_request({"model": NEW_BANANA}, Path(directory) / "product.png", 10)
            self.assertEqual(result["error_type"], "generation")
            self.assertEqual(result["cost"], 0.035)
            self.assertEqual(result["outputs"], [])

    def test_actual_encoding_save_failure_retains_known_cost(self):
        cli = load_cli()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "product.png"
            target.with_suffix(".jpg").mkdir()
            response = {"data": [{"b64_json": base64.b64encode(JPEG_BYTES).decode()}], "usage": {"cost": 0.035}}
            with patch.object(cli, "call_api", return_value=response):
                result = cli.execute_request({"model": NEW_BANANA}, target, 10)
            self.assertEqual(result["error_type"], "output")
            self.assertEqual(result["cost"], 0.035)
            self.assertEqual(result["outputs"], [])

if __name__ == "__main__":
    unittest.main()
