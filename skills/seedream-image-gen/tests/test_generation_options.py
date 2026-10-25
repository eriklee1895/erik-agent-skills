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

    def test_default_prompt_and_quality_negative(self):
        body = self.payload()
        self.assertEqual(body["prompt"], "test scene")
        self.assertEqual(body["negative_prompt"], "模糊, 低质量, 水印, 变形, 多余肢体")

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
            for model, requested, api_size in (("pro", "1500x600", "1520x608"), ("flash", "1500x600", "1520x608")):
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


if __name__ == "__main__":
    unittest.main()
