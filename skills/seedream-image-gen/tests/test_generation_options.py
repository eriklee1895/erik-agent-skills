"""Exercise Seedream CLI options and image postprocessing without API access."""

import asyncio
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seedream_image_gen.py"
SPEC = importlib.util.spec_from_file_location("seedream_generation_options", SCRIPT)
seedream = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(seedream)


class GenerationOptionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, {"ARK_API_KEY": ""}))
        self.stack.enter_context(patch.object(seedream, "_get_api_settings", return_value=("fixture", "https://offline.invalid")))
        self.stack.enter_context(patch.object(seedream.httpx, "AsyncClient", side_effect=AssertionError("Network disabled in tests")))
        self.calls = []
        self.stack.enter_context(patch.object(seedream, "_generate_with_retry", side_effect=self.generate_fixture))
        self.reference = self.root / "reference.png"
        Image.new("RGB", (100, 100), "teal").save(self.reference)

    async def generate_fixture(self, api_key, base_url, body, timeout):
        self.calls.append(body.copy())
        buffer = io.BytesIO()
        Image.new("RGBA", (1520, 608), (20, 100, 100, 200)).save(buffer, format="PNG")
        return [seedream.ImageOutput(buffer.getvalue(), "1520x608", "png")], None, {}, "1520x608", 1

    def invoke(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT), *arguments]), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                status = seedream.main()
            except SystemExit as exc:
                status = exc.code
        return status, stdout.getvalue(), stderr.getvalue()

    def payload(self, *flags):
        status, stdout, error = self.invoke("generate", "--prompt", "test scene", "--dry-run", *flags)
        self.assertEqual(status, 0, error)
        return json.loads(stdout)

    def jobs(self, name, jobs):
        path = self.root / f"{name}.jsonl"
        path.write_text("\n".join(json.dumps(job) for job in jobs), encoding="utf-8")
        return path

    def test_small_size_is_exact_across_commands_and_output_formats(self):
        for mode in ("generate", "concurrent", "edit", "batch"):
            for output_format in ("png", "jpeg", "jpg"):
                with self.subTest(mode=mode, output_format=output_format):
                    self.calls.clear()
                    output = self.root / f"{mode}-{output_format}"
                    command = "generate-batch" if mode == "batch" else "generate" if mode == "concurrent" else mode
                    arguments = [command, "--size", "1500x600", "--output-format", output_format, "--out-dir", str(output)]
                    if mode == "batch":
                        arguments += ["--input", str(self.jobs("small", [{"prompt": "test scene"}]))]
                    else:
                        arguments += ["--prompt", "test scene"]
                    if mode == "edit":
                        arguments += ["--reference-image", str(self.reference)]
                    if mode == "concurrent":
                        arguments += ["--n", "2"]
                    status, _, error = self.invoke(*arguments)
                    self.assertEqual(status, 0, error)
                    self.assertEqual(len(self.calls), 2 if mode == "concurrent" else 1)
                    self.assertTrue(all(body["size"] == "1520x608" for body in self.calls))
                    images = list(output.glob("*.png" if output_format == "png" else "*.jpg"))
                    self.assertEqual(len(images), len(self.calls))
                    for image in images:
                        with Image.open(image) as decoded:
                            self.assertEqual(decoded.size, (1500, 600))
                            self.assertEqual(decoded.format, "PNG" if output_format == "png" else "JPEG")
                        metadata = json.loads(image.with_suffix(".json").read_text())
                        self.assertEqual(metadata["size"], "1500x600")

    def test_default_prompt_has_no_undocumented_negative(self):
        for model in ("5.5", "doubao-seedream-5-5-261028"):
            with self.subTest(model=model):
                body = self.payload("--model", model)
                self.assertEqual(body["prompt"], "test scene")
                self.assertNotIn("negative_prompt", body)

    def test_undersized_request_can_still_be_rejected_explicitly(self):
        status, _, _ = self.invoke("generate", "--prompt", "test", "--size", "1500x600", "--no-auto-upscale", "--dry-run")
        self.assertEqual(status, 1)
        self.assertEqual(self.calls, [])

    def test_requested_batch_concurrency_above_eight_is_preserved(self):
        active = peak = 0

        async def generate(api_key, base_url, body, timeout):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0)
            active -= 1
            return [seedream.ImageOutput(self.reference.read_bytes(), "100x100", "png")], None, {}, "100x100", 1

        jobs = self.jobs("concurrent", [{"prompt": f"scene {index}"} for index in range(12)])
        with patch.object(seedream, "_generate_with_retry", side_effect=generate):
            status, _, error = self.invoke("generate-batch", "--input", str(jobs), "--concurrency", "12")
        self.assertEqual(status, 0, error)
        self.assertEqual(peak, 12)
        self.assertEqual(len(list((self.root / "output/seedream-image-gen/batch").glob("*.png"))), 12)

    def test_new_dry_run_metadata_remains_available(self):
        output = self.root / "preview.png"
        status, _, error = self.invoke("generate", "--prompt", "test", "--dry-run", "--out", str(output))
        self.assertEqual(status, 0, error)
        self.assertFalse(output.exists())
        self.assertTrue(output.with_suffix(".json").is_file())
        self.assertTrue(json.loads(output.with_suffix(".json").read_text())["dry_run"])

    def test_dry_run_metadata_records_requested_size_while_payload_uses_api_size(self):
        for command in ("generate", "edit"):
            for model, requested, api_size in (("5.5", "1500x600", "1520x608"),):
                with self.subTest(command=command, model=model):
                    output = self.root / f"{command}-{model}-preview.png"
                    arguments = [command, "--prompt", "test", "--model", model, "--size", requested,
                                 "--dry-run", "--out", str(output)]
                    if command == "edit":
                        arguments += ["--reference-image", str(self.reference)]
                    status, stdout, error = self.invoke(*arguments)
                    self.assertEqual(status, 0, error)
                    self.assertEqual(json.loads(stdout)["size"], api_size)
                    metadata = json.loads(output.with_suffix(".json").read_text())
                    self.assertEqual(metadata["size"], requested)
                    self.assertFalse(output.exists())

    def test_outpaint_uses_explicit_padded_size_when_canvas_fits_contract(self):
        source = self.root / "large.png"
        Image.new("RGB", (1024, 1024), "navy").save(source)
        status, stdout, error = self.invoke(
            "edit", "--prompt", "extend left", "--reference-image", str(source),
            "--outpaint", "left:200", "--dry-run",
        )
        self.assertEqual(status, 0, error)
        self.assertEqual(json.loads(stdout)["size"], "1224x1024")

    def test_outpaint_respects_an_explicit_user_size(self):
        source = self.root / "large.png"
        Image.new("RGB", (1024, 1024), "navy").save(source)
        status, stdout, error = self.invoke(
            "edit", "--prompt", "extend left", "--reference-image", str(source),
            "--outpaint", "left:200", "--size", "1K", "--dry-run",
        )
        self.assertEqual(status, 0, error)
        self.assertEqual(json.loads(stdout)["size"], "1K")
        self.assertNotIn("outside the", error)

    def test_outpaint_dry_run_metadata_records_effective_padded_size(self):
        source = self.root / "meta.png"
        Image.new("RGB", (1024, 1024), "navy").save(source)
        output = self.root / "outpaint-preview.png"
        status, _, error = self.invoke(
            "edit", "--prompt", "extend left", "--reference-image", str(source),
            "--outpaint", "left:200", "--dry-run", "--out", str(output),
        )
        self.assertEqual(status, 0, error)
        metadata = json.loads(output.with_suffix(".json").read_text())
        self.assertEqual(metadata["size"], "1224x1024")

    def test_outpaint_over_pixel_cap_keeps_preset_and_warns(self):
        source = self.root / "wide.png"
        Image.new("RGB", (2816, 1584), "white").save(source)
        status, stdout, error = self.invoke(
            "edit", "--prompt", "extend left", "--reference-image", str(source),
            "--outpaint", "left:400", "--dry-run",
        )
        self.assertEqual(status, 0, error)
        self.assertEqual(json.loads(stdout)["size"], "2K")
        self.assertIn("outside the", error)

    def test_jpeg_edit_warns_about_chain_artifacts(self):
        status, _, error = self.invoke(
            "edit", "--prompt", "recolor", "--reference-image", str(self.reference),
            "--output-format", "jpeg", "--dry-run",
        )
        self.assertEqual(status, 0)
        self.assertIn("JPEG output", error)
        status, _, error = self.invoke(
            "edit", "--prompt", "recolor", "--reference-image", str(self.reference),
            "--output-format", "png", "--dry-run",
        )
        self.assertEqual(status, 0)
        self.assertNotIn("JPEG output", error)

    def test_prompt_length_nudge_uses_official_guidance_not_hard_limit(self):
        status, _, error = self.invoke("generate", "--prompt", "短提示词", "--dry-run")
        self.assertEqual(status, 0)
        self.assertNotIn("Chinese characters", error)
        status, _, error = self.invoke("generate", "--prompt", "细节 " * 200, "--dry-run")
        self.assertEqual(status, 0)
        self.assertIn("characters", error)
        self.assertIn("about 300", error)

    def test_prompt_length_warning_covers_english_bilingual_and_kana(self):
        status, _, error = self.invoke(
            "generate", "--prompt", " ".join(["word"] * 700), "--dry-run")
        self.assertEqual(status, 0)
        self.assertIn("600 English words", error)
        status, _, error = self.invoke(
            "generate", "--prompt", "汉字 " * 10 + " ".join(["word"] * 700), "--dry-run")
        self.assertEqual(status, 0)
        self.assertIn("600 English words", error)
        status, _, error = self.invoke("generate", "--prompt", "あ" * 400, "--dry-run")
        self.assertEqual(status, 0)
        self.assertIn("CJK/kana/hangul", error)

    def test_outpaint_under_floor_keeps_tier_and_warns(self):
        source = self.root / "small.png"
        Image.new("RGB", (800, 800), "white").save(source)
        status, stdout, error = self.invoke(
            "edit", "--prompt", "extend left", "--reference-image", str(source),
            "--outpaint", "left:100", "--dry-run",
        )
        self.assertEqual(status, 0, error)
        self.assertEqual(json.loads(stdout)["size"], "2K")
        self.assertIn("outside the", error)

    def test_outpaint_with_marker_keeps_padded_size(self):
        source = self.root / "marked.png"
        Image.new("RGB", (1024, 1024), "teal").save(source)
        status, stdout, error = self.invoke(
            "edit", "--prompt", "extend left and recolor the box",
            "--reference-image", str(source),
            "--outpaint", "left:200", "--marker-rect", "10%,10%,30%,30%", "--dry-run",
        )
        self.assertEqual(status, 0, error)
        self.assertEqual(json.loads(stdout)["size"], "1224x1024")

    def test_batch_phone_shortcut_falls_back_to_cli_default(self):
        jobs = self.jobs("phone", [{"prompt": "scene one"}])
        status, stdout, error = self.invoke(
            "generate-batch", "--input", str(jobs), "--phone", "--dry-run",
        )
        self.assertEqual(status, 0, error)
        decoder = json.JSONDecoder()
        start = stdout.find("{")
        body = decoder.raw_decode(stdout[start:])[0]
        self.assertEqual(body["size"], "1152x2048")

    def test_batch_non_string_safety_identifier_fails_cleanly(self):
        jobs = self.jobs("badsafety", [{"prompt": "scene", "safety_identifier": 12345}])
        status, _, error = self.invoke("generate-batch", "--input", str(jobs), "--dry-run")
        self.assertNotEqual(status, 0)
        self.assertIn("safety-identifier", error)

    def test_batch_per_job_safety_identifier_overrides_cli_default(self):
        jobs = self.jobs("safety", [
            {"prompt": "scene one", "safety_identifier": "job-user-9"},
            {"prompt": "scene two"},
        ])
        status, stdout, error = self.invoke(
            "generate-batch", "--input", str(jobs), "--dry-run",
            "--safety-identifier", "batch-default-1",
        )
        self.assertEqual(status, 0, error)
        decoder = json.JSONDecoder()
        bodies = []
        for segment in stdout.split("--- Job"):
            start = segment.find("{")
            if start >= 0:
                bodies.append(decoder.raw_decode(segment[start:])[0])
        self.assertEqual(len(bodies), 2)
        self.assertEqual(bodies[0]["safety_identifier"], "job-user-9")
        self.assertEqual(bodies[1]["safety_identifier"], "batch-default-1")


if __name__ == "__main__":
    unittest.main()
