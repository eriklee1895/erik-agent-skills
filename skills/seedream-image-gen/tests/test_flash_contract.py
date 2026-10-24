"""Offline provider-boundary tests for the Pro/Flash contract."""

import base64
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
from unittest.mock import AsyncMock, patch

import httpx
from PIL import Image, ImageDraw


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seedream_image_gen.py"
SPEC = importlib.util.spec_from_file_location("seedream_flash_contract", SCRIPT)
seedream = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = seedream
SPEC.loader.exec_module(seedream)
FLASH = "doubao-seedream-5-0-flash-260915"


def picture(size, mode="RGBA", encoding="PNG"):
    stream = io.BytesIO()
    Image.new(mode, size, (80, 150, 180, 150) if mode == "RGBA" else (80, 150, 180)).save(stream, encoding)
    return stream.getvalue()


class FlashContractTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, {
            "ARK_API_KEY": "offline-fixture", "ARK_BASE_URL": "https://offline.invalid/api/v3"
        }))
        self.requests = []
        original_client = httpx.AsyncClient
        self.stack.enter_context(patch.object(seedream.httpx, "AsyncClient", side_effect=lambda **kw: original_client(
            **kw, transport=httpx.MockTransport(self.respond)
        )))
        self.reference = self.root / "reference.png"
        self.reference.write_bytes(picture((1024, 1024), "RGB"))
        self.alpha = self.root / "alpha.png"
        image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        ImageDraw.Draw(image).rectangle((200, 200, 800, 800), fill=(200, 80, 40, 255))
        image.save(self.alpha)

    def respond(self, request):
        self.requests.append(request)
        return httpx.Response(200, json={
            "model": FLASH,
            "data": [{"b64_json": base64.b64encode(picture((1024, 1024))).decode(),
                      "size": "1024x1024", "output_format": "png"}],
            "usage": {"generated_images": 1, "input_images": 0},
        })

    def invoke(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT), *arguments]), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = seedream.main()
            except SystemExit as exc:
                code = exc.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_flash_alias_resolves_and_accepts_one_point_five_k(self):
        code, stdout, error = self.invoke("generate", "--model", "flash", "--size", "1.5K", "--prompt", "test", "--dry-run")
        self.assertEqual(code, 0, error)
        body = json.loads(stdout)
        self.assertEqual(body["model"], FLASH)
        self.assertEqual(body["size"], "1.5K")
        self.assertEqual(body["optimize_prompt_options"], {"mode": "standard"})
        self.assertNotIn("sequential_image_generation", body)
        self.assertNotIn("tools", body)

    def test_retired_lite_never_silently_resolves_to_a_paid_model(self):
        for model in ("lite", "seedream-lite", "doubao-seedream-5-0-260128", "doubao-seedream-5-0-lite-260128"):
            with self.subTest(model=model):
                code, _, error = self.invoke("generate", "--model", model, "--prompt", "test", "--dry-run")
                self.assertNotEqual(code, 0)
                self.assertIn("retired", error.lower())
        self.assertEqual(self.requests, [])

    def test_pro_fast_is_supported_and_flash_fast_is_rejected(self):
        code, stdout, error = self.invoke("generate", "--model", "pro", "--optimize-prompt", "fast", "--prompt", "test", "--dry-run")
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(stdout)["optimize_prompt_options"], {"mode": "fast"})
        code, _, _ = self.invoke("generate", "--model", "flash", "--optimize-prompt", "fast", "--prompt", "test", "--dry-run")
        self.assertNotEqual(code, 0)
        self.assertEqual(self.requests, [])

    def test_transparent_edit_requires_one_alpha_input_and_png(self):
        code, stdout, error = self.invoke("edit", "--model", "flash", "--reference-image", str(self.alpha),
                                          "--background", "transparent", "--prompt", "recolor", "--dry-run")
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(stdout)["background"], "transparent")
        for extra in (["--reference-image", str(self.reference)],
                      ["--reference-image", str(self.alpha), "--output-format", "jpeg"],
                      ["--reference-image", str(self.alpha), "--reference-image", str(self.alpha)]):
            with self.subTest(extra=extra):
                code, _, _ = self.invoke("edit", "--model", "flash", "--prompt", "test",
                                          "--background", "transparent", "--dry-run", *extra)
                self.assertNotEqual(code, 0)
        code, _, _ = self.invoke("generate", "--model", "flash", "--background", "transparent", "--prompt", "test", "--dry-run")
        self.assertNotEqual(code, 0)
        self.assertEqual(self.requests, [])

    def test_transparent_marker_edit_preserves_alpha_in_submitted_reference(self):
        for model in ("pro", "flash"):
            with self.subTest(model=model):
                code, stdout, error = self.invoke(
                    "edit", "--model", model, "--reference-image", str(self.alpha),
                    "--background", "transparent", "--marker-rect", "10%,10%,20%,20%",
                    "--prompt", "recolor the marked area", "--dry-run",
                )
                self.assertEqual(code, 0, error)
                body = json.loads(stdout)
                self.assertEqual(body["background"], "transparent")
                reference = body["image"]
                if isinstance(reference, list):
                    reference = reference[0]
                with Image.open(io.BytesIO(base64.b64decode(reference.split(",", 1)[1]))) as image:
                    self.assertIn("A", image.getbands())
                    self.assertEqual(image.getchannel("A").getextrema(), (0, 255))
                    # Markers over empty pixels must stay visible to locate the edit.
                    self.assertGreater(image.getpixel((150, 150))[3], 0)
        self.assertEqual(self.requests, [])

    def test_decompose_saves_native_formats_crops_and_position_metadata(self):
        base = picture((1024, 1024), "RGB", "JPEG")
        layer = picture((256, 320))
        response = {"model": FLASH, "data": [
            {"b64_json": base64.b64encode(base).decode(), "size": "1024x1024", "output_format": "jpeg", "z_index": 0},
            {"b64_json": base64.b64encode(layer).decode(), "size": "256x320", "output_format": "png", "z_index": 1,
             "name": "cup", "description": "teal cup", "bounding_box": {"absolute": [100, 200, 356, 520], "normalized": [98, 195, 348, 508]}},
        ], "usage": {"generated_images": 2, "input_images": 1}}
        self.respond = lambda request: (self.requests.append(request) or httpx.Response(200, json=response))
        output = self.root / "layers"
        code, _, error = self.invoke("decompose", "--model", "flash", "--reference-image", str(self.reference),
                                     "--out-dir", str(output), "--output-format", "jpeg")
        self.assertEqual(code, 0, error)
        self.assertEqual(len(self.requests), 1)
        body = json.loads(self.requests[0].content)
        self.assertTrue(body["layer_decomposition"])
        self.assertEqual(body["size"], "auto")
        self.assertNotIn("prompt", body)
        manifest = json.loads((output / "layers.json").read_text())
        self.assertEqual([item["file"] for item in manifest["layers"]], ["base.jpg", "layer-001.png"])
        self.assertEqual(manifest["layers"][1]["bounding_box"]["absolute"], [100, 200, 356, 520])
        self.assertEqual(manifest["layers"][1]["name"], "cup")
        with Image.open(output / "base.jpg") as image:
            self.assertEqual(image.format, "JPEG")
        with Image.open(output / "layer-001.png") as image:
            self.assertEqual(image.size, (256, 320))
            self.assertIn("A", image.getbands())
        self.assertNotIn("b64_json", (output / "layers.json").read_text())

    def test_decompose_rejects_multiple_inputs_and_explicit_pixel_sizes(self):
        for extra in (["--reference-image", str(self.reference)], ["--size", "1024x1024"]):
            with self.subTest(extra=extra):
                code, _, _ = self.invoke("decompose", "--model", "flash", "--reference-image", str(self.reference), "--dry-run", *extra)
                self.assertNotEqual(code, 0)
        self.assertEqual(self.requests, [])

    def test_decompose_preview_needs_no_credentials_and_creates_no_output_folder(self):
        output = self.root / "preview-layers"
        with patch.dict(os.environ, {"ARK_API_KEY": ""}):
            code, stdout, error = self.invoke("decompose", "--model", "flash", "--reference-image", str(self.reference),
                                              "--out-dir", str(output), "--dry-run")
        self.assertEqual(code, 0, error)
        self.assertTrue(json.loads(stdout)["layer_decomposition"])
        self.assertFalse(output.exists())
        self.assertEqual(self.requests, [])

    def test_decompose_existing_outputs_are_rejected_before_generation(self):
        output = self.root / "existing-layers"
        output.mkdir()
        manifest = output / "layers.json"
        manifest.write_text('{"preserve":"existing outputs"}')
        code, _, _ = self.invoke("decompose", "--model", "flash", "--reference-image", str(self.reference), "--out-dir", str(output))
        self.assertEqual(code, 1)
        self.assertEqual(self.requests, [])
        self.assertEqual(json.loads(manifest.read_text()), {"preserve": "existing outputs"})

    def test_shared_reference_limit_is_ten_for_both_models(self):
        for model in ("pro", "flash"):
            with self.subTest(model=model):
                arguments = ["generate", "--model", model, "--prompt", "test", "--dry-run"]
                for _index in range(11):
                    arguments += ["--reference-image", str(self.reference)]
                code, _, _ = self.invoke(*arguments)
                self.assertEqual(code, 1)
        self.assertEqual(self.requests, [])

    def test_transport_failure_does_not_replay_unknown_generation(self):
        def timeout(request):
            self.requests.append(request)
            raise httpx.ReadTimeout("fixture timeout", request=request)
        self.respond = timeout
        with patch.object(seedream, "MAX_RETRIES", 1), patch.object(seedream.asyncio, "sleep", new=AsyncMock()), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(seedream._APIError) as caught:
                asyncio.run(seedream._generate_with_retry("fixture", "https://offline.invalid", {"model": "pro"}, 1))
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(caught.exception.code, "OutcomeUnknown")

    def test_download_failure_retries_download_without_replaying_generation(self):
        def response(request):
            self.requests.append(request)
            if request.method == "POST":
                return httpx.Response(200, json={"data": [{"url": "https://offline.invalid/generated.png?fixture-signature=hidden"}]})
            raise httpx.ReadTimeout("fixture download timeout", request=request)
        self.respond = response
        with patch.object(seedream, "MAX_RETRIES", 1), patch.object(seedream.asyncio, "sleep", new=AsyncMock()), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(seedream._APIError) as caught:
                asyncio.run(seedream._generate_with_retry("fixture", "https://offline.invalid", {"model": "pro"}, 1))
        self.assertEqual(sum(request.method == "POST" for request in self.requests), 1)
        self.assertEqual(sum(request.method == "GET" for request in self.requests), 2)
        self.assertEqual(caught.exception.code, "DownloadFailed")
        self.assertNotIn("fixture-signature", caught.exception.message)


if __name__ == "__main__":
    unittest.main()
