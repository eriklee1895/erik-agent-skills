"""Offline CLI regressions. Run with python -m unittest discover -s this-directory."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seedream_image_gen.py"
SPEC = importlib.util.spec_from_file_location("seedream_dry_run", SCRIPT)
seedream = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(seedream)


class DryRunTests(unittest.TestCase):
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
        self.stack.enter_context(patch.object(sys.stdin, "isatty", return_value=False))
        self.stack.enter_context(patch.object(
            seedream.httpx, "AsyncClient", side_effect=AssertionError("Network disabled in tests")
        ))
        self.reference = self.root / "reference.png"
        Image.new("RGB", (100, 100), "teal").save(self.reference)

    def invoke(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT), *arguments]), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                status = seedream.main()
            except SystemExit as exc:
                status = exc.code
        return status, stdout.getvalue(), stderr.getvalue()

    def command(self, command, output, *flags):
        arguments = [command, "--prompt", "preview prompt", "--out", str(output), *flags]
        if command == "edit":
            arguments += ["--reference-image", str(self.reference)]
        return arguments

    def test_dry_run_preserves_existing_metadata_even_with_force(self):
        for command in ("generate", "edit"):
            for existing_image in (False, True):
                for force in (False, True):
                    with self.subTest(command=command, existing_image=existing_image, force=force):
                        output = self.root / f"{command}-{existing_image}-{force}.png"
                        metadata = output.with_suffix(".json")
                        original = b'{"prompt":"actual image metadata","dry_run":false}'
                        metadata.write_bytes(original)
                        if existing_image:
                            output.write_bytes(self.reference.read_bytes())
                        flags = ["--dry-run", *(["--force"] if force else [])]
                        status, _, error = self.invoke(*self.command(command, output, *flags))
                        self.assertEqual(status, 0, error)
                        self.assertEqual(metadata.read_bytes(), original)
                        self.assertEqual(output.exists(), existing_image)
                        if existing_image:
                            self.assertEqual(output.read_bytes(), self.reference.read_bytes())

    def test_generate_dry_run_keeps_new_metadata_without_an_image(self):
        self.assert_new_metadata("generate")

    def test_edit_dry_run_keeps_new_metadata_without_an_image(self):
        self.assert_new_metadata("edit")

    def assert_new_metadata(self, command):
        output = self.root / "new.png"
        status, stdout, error = self.invoke(*self.command(command, output, "--dry-run"))
        self.assertEqual(status, 0, error)
        self.assertFalse(output.exists())
        self.assertEqual(json.loads(stdout)["prompt"], "preview prompt")
        metadata = json.loads(output.with_suffix(".json").read_text())
        self.assertTrue(metadata["dry_run"])
        self.assertEqual(metadata["prompt"], "preview prompt")

    def test_batch_dry_run_needs_no_api_key(self):
        jobs = self.root / "jobs.jsonl"
        jobs.write_text('{"prompt":"a teal fox"}\n', encoding="utf-8")
        output = self.root / "batch-output"
        status, stdout, error = self.invoke(
            "generate-batch", "--input", str(jobs), "--out-dir", str(output), "--dry-run"
        )
        self.assertEqual(status, 0, error)
        self.assertIn("a teal fox", stdout)
        self.assertFalse(output.exists())

    def test_real_generation_with_force_still_replaces_metadata(self):
        output = self.root / "cover.png"
        output.write_bytes(b"old image")
        output.with_suffix(".json").write_text('{"prompt":"old metadata"}')
        response = ([self.reference.read_bytes()], None, {}, "100x100", 1)
        with patch.object(seedream, "_get_api_settings", return_value=("fixture", "https://offline.invalid")), \
                patch.object(seedream, "_generate_with_retry", new=AsyncMock(return_value=response)):
            status, _, error = self.invoke(*self.command("generate", output, "--force"))
        self.assertEqual(status, 0, error)
        self.assertEqual(output.read_bytes(), self.reference.read_bytes())
        metadata = json.loads(output.with_suffix(".json").read_text())
        self.assertFalse(metadata["dry_run"])
        self.assertEqual(metadata["prompt"], "preview prompt")


if __name__ == "__main__":
    unittest.main()
