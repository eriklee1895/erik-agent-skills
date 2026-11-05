"""No-network characterization of the SDK boundary used by paid requests."""
from __future__ import annotations

import base64
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from email import policy
from email.parser import BytesParser
from pathlib import Path
from unittest import mock

from PIL import Image

from test_gpt_image_api import load_module

try:
    import httpx2
    from openai import OpenAI
except ImportError:
    httpx2 = None
    OpenAI = None


@unittest.skipUnless(OpenAI is not None, "run with openai>=3.46.0 for SDK transport checks")
class SDKTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def image_bytes(self, fmt="PNG"):
        buffer = io.BytesIO()
        first = Image.new("RGB", (32, 48), "red")
        if fmt == "GIF":
            first.save(buffer, format="GIF", save_all=True,
                       append_images=[Image.new("RGB", (32, 48), "blue")],
                       duration=100, loop=0)
        else:
            first.save(buffer, format=fmt)
        return buffer.getvalue()

    def run_request(self, spec, output, response_bytes, *, extra_response=None):
        requests = []

        def handle(request):
            requests.append((request.url.path, request.headers, request.read()))
            return httpx2.Response(200, json={
                "created": 1,
                "data": [{"b64_json": base64.b64encode(response_bytes).decode()}],
                **(extra_response or {}),
            })

        transport = httpx2.MockTransport(handle)
        with OpenAI(api_key="unit-test-key", base_url="https://api.ofox.io/v1",
                    max_retries=0, http_client=httpx2.Client(transport=transport)) as client:
            with (mock.patch.object(self.mod, "get_api_settings",
                                    return_value=("unit-test-key", "https://api.ofox.io/v1")),
                  mock.patch.object(self.mod, "_create_client", return_value=client),
                  redirect_stderr(io.StringIO())):
                self.mod.run_live_request(spec=spec, out=output, force=False,
                                          max_attempts=1, timeout=30)
        return requests

    def test_gif_fields_reach_generation_json_and_original_bytes_survive(self):
        spec = self.mod.build_generate_spec(prompt="A panda waves", output_format="gif",
            size="512x512", frame_count=2, frame_duration_ms=100, complexity="low")
        raw = self.image_bytes("GIF")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "loop.gif"
            requests = self.run_request(spec, output, raw)
            self.assertEqual(output.read_bytes(), raw)
            path, headers, body = requests[0]
            self.assertEqual(path, "/v1/images/generations")
            self.assertTrue(headers["content-type"].startswith("application/json"))
            payload = json.loads(body)
            self.assertEqual(payload["model"], "openai/gpt-image-2.6-flare")
            self.assertEqual(payload["frame_count"], 2)
            self.assertEqual(payload["frame_duration_ms"], 100)
            self.assertEqual(payload["complexity"], "low")
            self.assertNotIn("extra_body", payload)

    def test_markup_is_a_separate_multipart_file_with_unchanged_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            markup = root / "markup.png"
            source.write_bytes(self.image_bytes())
            Image.new("RGBA", (32, 48), (255, 0, 0, 0)).save(markup)
            spec = self.mod.build_edit_spec(prompt="Change the marked object only",
                images=[source], markup=markup, complexity="medium")
            requests = self.run_request(spec, root / "edited.png", self.image_bytes())
            path, headers, body = requests[0]
            self.assertEqual(path, "/v1/images/edits")
            message = BytesParser(policy=policy.default).parsebytes(
                ("Content-Type: " + headers["content-type"] + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
            parts = {part.get_param("name", header="content-disposition"):
                     part.get_payload(decode=True) for part in message.iter_parts()}
            self.assertEqual(parts["markup"], markup.read_bytes())
            self.assertEqual(parts["image[]"], source.read_bytes())
            self.assertEqual(parts["complexity"], b"medium")
            self.assertNotIn("mask", parts)

    def test_svg_author_selection_reaches_nested_request_object(self):
        spec = self.mod.build_generate_spec(prompt="Icon", output_format="svg",
            svg_model="available-author-model", svg_reasoning="low")
        raw = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/></svg>'
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "icon.svg"
            requests = self.run_request(spec, output, raw,
                extra_response={"svg_usage": {"total_tokens": 11}})
            payload = json.loads(requests[0][2])
            self.assertEqual(payload["svg"], {
                "model": "available-author-model", "reasoning": {"effort": "low"}})
            self.assertEqual(output.read_bytes(), raw)
            metadata = json.loads(output.with_suffix(".json").read_text())
            self.assertEqual(metadata["response"]["svg_usage"], {"total_tokens": 11})


if __name__ == "__main__":
    unittest.main()
