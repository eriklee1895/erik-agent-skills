from __future__ import annotations

import importlib.util
import io
import os
import base64
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "gpt_image_api.py"


def load_module():
    spec = importlib.util.spec_from_file_location("gpt_image_api", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ModelAndRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def test_only_current_gpt_image_25_models_are_supported(self):
        self.assertEqual(
            self.mod.ALLOWED_MODELS,
            {
                "gpt-image-2.5-flare",
                "gpt-image-2.5-flare-2026-09-08",
                "gpt-image-2.5-sunburst",
                "gpt-image-2.5-sunburst-2026-09-08",
            },
        )
        self.assertEqual(self.mod.DEFAULT_MODEL, "gpt-image-2.5-flare")

    def test_model_shorthands_resolve_to_current_aliases(self):
        self.assertEqual(self.mod.resolve_model("flare"), "gpt-image-2.5-flare")
        self.assertEqual(self.mod.resolve_model("sunburst"), "gpt-image-2.5-sunburst")

    def test_legacy_or_unknown_model_is_rejected(self):
        for value in ("gpt-image-2", "gpt-image-2.5", "dall-e-3"):
            with self.subTest(value=value), self.assertRaises(self.mod.UsageError):
                self.mod.resolve_model(value)

    def test_all_gpt_image_25_quality_values_are_accepted(self):
        for quality in ("auto", "low", "medium", "high", "xhigh", "max"):
            with self.subTest(quality=quality):
                self.assertEqual(self.mod.validate_quality(quality), quality)

    def test_unknown_quality_is_rejected(self):
        with self.assertRaises(self.mod.UsageError):
            self.mod.validate_quality("ultra")

    def test_custom_credentials_are_resolved_as_an_atomic_pair(self):
        with mock.patch.dict(
            os.environ,
            {
                "CUSTOM_OPENAI_BASE_URL": "https://custom.example/v1",
                "OPENAI_API_KEY": "standard-key",
            },
            clear=True,
        ):
            with self.assertRaises(self.mod.UsageError):
                self.mod.get_api_settings(require_key=True)

        with mock.patch.dict(
            os.environ,
            {
                "CUSTOM_OPENAI_BASE_URL": "https://custom.example/v1",
                "CUSTOM_OPENAI_API_KEY": "custom-key",
                "OPENAI_API_KEY": "standard-key",
            },
            clear=True,
        ):
            self.assertEqual(
                self.mod.get_api_settings(require_key=True),
                ("custom-key", "https://custom.example/v1"),
            )

    def test_custom_size_envelope(self):
        for size in (
            "1024x1024",
            "1536x1024",
            "2048x1152",
            "3840x2160",
            "2160x3840",
            "auto",
        ):
            with self.subTest(size=size):
                self.assertEqual(self.mod.validate_size(size), size)

    def test_invalid_sizes_are_rejected(self):
        for size in (
            "1000x1000",  # not divisible by 16
            "4096x1024",  # edge too large
            "3200x800",  # ratio above 3:1
            "512x512",  # too few pixels
            "3840x3840",  # too many pixels
            "cinematic",
        ):
            with self.subTest(size=size), self.assertRaises(self.mod.UsageError):
                self.mod.validate_size(size)

    def test_transparent_background_requires_png_or_webp(self):
        for fmt in ("png", "webp"):
            self.mod.validate_output_options("transparent", fmt, None)
        with self.assertRaises(self.mod.UsageError):
            self.mod.validate_output_options("transparent", "jpeg", None)

    def test_compression_is_only_for_jpeg_or_webp(self):
        for fmt in ("jpeg", "webp"):
            self.mod.validate_output_options("opaque", fmt, 70)
        with self.assertRaises(self.mod.UsageError):
            self.mod.validate_output_options("opaque", "png", 70)
        for compression in (-1, 101):
            with self.assertRaises(self.mod.UsageError):
                self.mod.validate_output_options("opaque", "jpeg", compression)

    def test_generate_spec_preserves_prompt_verbatim(self):
        prompt = "  第一行\nSecond line: keep  two spaces.  "
        spec = self.mod.build_generate_spec(
            prompt=prompt,
            model="flare",
            size="2048x1152",
            quality="xhigh",
            background="transparent",
            output_format="png",
            partial_images=2,
            stream=True,
        )
        self.assertEqual(spec["prompt"], prompt)
        self.assertEqual(spec["model"], "gpt-image-2.5-flare")
        self.assertEqual(spec["partial_images"], 2)
        self.assertTrue(spec["stream"])
        self.assertNotIn("input_fidelity", spec)

    def test_sdk_payload_only_sends_moderation_for_generation(self):
        generate = self.mod.build_generate_spec(prompt="generate")
        self.assertIn("moderation", self.mod._sdk_common_payload(generate))

        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "source.png"
            Image.new("RGB", (1024, 1024), "white").save(image)
            edit = self.mod.build_edit_spec(prompt="edit", images=[image])
            self.assertNotIn("moderation", edit)
            self.assertNotIn("moderation", self.mod._sdk_common_payload(edit))

    def test_partial_images_require_streaming(self):
        with self.assertRaises(self.mod.UsageError):
            self.mod.build_generate_spec(prompt="x", partial_images=1, stream=False)

    def test_streaming_is_single_output_only(self):
        with self.assertRaises(self.mod.UsageError):
            self.mod.build_generate_spec(prompt="x", n=2, stream=True)

    def test_prompt_limit_is_enforced_without_trimming(self):
        exact = "x" * 32_000
        self.assertEqual(self.mod.validate_prompt(exact), exact)
        with self.assertRaises(self.mod.UsageError):
            self.mod.validate_prompt(exact + "x")


class EditInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.base = self.root / "base.png"
        self.reference = self.root / "reference.webp"
        self.mask = self.root / "mask.png"
        Image.new("RGB", (1024, 1024), "white").save(self.base)
        Image.new("RGB", (1024, 1024), "blue").save(self.reference)
        mask = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))
        for x in range(256, 768):
            for y in range(256, 768):
                mask.putpixel((x, y), (255, 255, 255, 0))
        mask.save(self.mask)

    def tearDown(self):
        self.tmp.cleanup()

    def test_edit_spec_preserves_input_order_and_roles(self):
        spec = self.mod.build_edit_spec(
            prompt="Change only the jacket.",
            images=[self.base, self.reference],
            roles=["edit target", "identity reference"],
            mask=self.mask,
            model="sunburst",
            size="1024x1024",
        )
        self.assertEqual(spec["images"], [str(self.base), str(self.reference)])
        self.assertEqual(spec["image_roles"], ["edit target", "identity reference"])
        self.assertEqual(spec["mask"], str(self.mask))
        self.assertEqual(spec["model"], "gpt-image-2.5-sunburst")
        self.assertNotIn("input_fidelity", spec)

    def test_edit_rejects_more_than_sixteen_images(self):
        images = [self.base] * 17
        with self.assertRaises(self.mod.UsageError):
            self.mod.build_edit_spec(prompt="x", images=images)

    def test_edit_rejects_role_count_mismatch(self):
        with self.assertRaises(self.mod.UsageError):
            self.mod.build_edit_spec(
                prompt="x", images=[self.base, self.reference], roles=["target"]
            )

    def test_mask_must_match_first_image_dimensions_and_have_alpha(self):
        wrong_size = self.root / "wrong-size.png"
        Image.new("RGBA", (512, 512), (0, 0, 0, 0)).save(wrong_size)
        with self.assertRaises(self.mod.UsageError):
            self.mod.build_edit_spec(
                prompt="x", images=[self.base], mask=wrong_size, size="1024x1024"
            )

        no_alpha = self.root / "no-alpha.png"
        Image.new("RGB", (1024, 1024), "black").save(no_alpha)
        with self.assertRaises(self.mod.UsageError):
            self.mod.build_edit_spec(
                prompt="x", images=[self.base], mask=no_alpha, size="1024x1024"
            )

    def test_mask_requires_at_least_one_fully_transparent_pixel(self):
        opaque = self.root / "opaque-mask.png"
        Image.new("RGBA", (1024, 1024), (255, 255, 255, 255)).save(opaque)
        with self.assertRaises(self.mod.UsageError):
            self.mod.build_edit_spec(
                prompt="x", images=[self.base], mask=opaque, size="1024x1024"
            )

    def test_edit_rejects_unsupported_input_extension(self):
        invalid = self.root / "image.gif"
        invalid.write_bytes(b"GIF89a")
        with self.assertRaises(self.mod.UsageError):
            self.mod.build_edit_spec(prompt="x", images=[invalid])

    def test_edit_rejects_invalid_image_bytes(self):
        invalid = self.root / "broken.png"
        invalid.write_bytes(b"not a png")
        with self.assertRaises(self.mod.UsageError):
            self.mod.build_edit_spec(prompt="x", images=[invalid])

    def test_edit_rejects_empty_image_roles(self):
        with self.assertRaises(self.mod.UsageError):
            self.mod.build_edit_spec(prompt="x", images=[self.base], roles=["   "])

    def test_edit_retry_reopens_consumed_input_streams(self):
        output_buffer = io.BytesIO()
        Image.new("RGB", (1024, 1024), "green").save(output_buffer, format="PNG")
        encoded_output = base64.b64encode(output_buffer.getvalue()).decode("ascii")

        class TransientError(Exception):
            status_code = 503
            code = "service_unavailable"

        class FakeImages:
            def __init__(self):
                self.read_lengths = []

            def edit(self, **payload):
                self.read_lengths.append(
                    [len(handle.read()) for handle in payload["image"]]
                )
                if len(self.read_lengths) == 1:
                    raise TransientError("retry")
                return SimpleNamespace(
                    data=[SimpleNamespace(b64_json=encoded_output)],
                    size="1024x1024",
                    quality="low",
                    background="opaque",
                    output_format="png",
                    usage=None,
                    _request_id="req_retry",
                )

        fake_images = FakeImages()
        fake_client = SimpleNamespace(images=fake_images)
        spec = self.mod.build_edit_spec(
            prompt="change color",
            images=[self.base],
            model="sunburst",
            size="1024x1024",
            quality="low",
        )
        output = self.root / "retry-output.png"
        with (
            mock.patch.object(
                self.mod,
                "get_api_settings",
                return_value=("test-key", "https://example.invalid/v1"),
            ),
            mock.patch.object(self.mod, "_create_client", return_value=fake_client),
            mock.patch.object(self.mod, "_retry_after", return_value=0),
            redirect_stderr(io.StringIO()),
        ):
            self.mod.run_live_request(
                spec=spec,
                out=output,
                force=False,
                max_attempts=2,
                timeout=30,
            )

        self.assertGreater(fake_images.read_lengths[0][0], 0)
        self.assertGreater(fake_images.read_lengths[1][0], 0)
        self.assertTrue(output.is_file())


class OutputAndBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def test_output_paths_are_deterministic_for_variants(self):
        paths = self.mod.build_output_paths(Path("cover.png"), "png", 3)
        self.assertEqual(
            paths,
            [Path("cover-01.png"), Path("cover-02.png"), Path("cover-03.png")],
        )

    def test_non_overwrite_writer_requires_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "asset.png"
            self.mod.write_bytes(path, b"first", force=False)
            with self.assertRaises(FileExistsError):
                self.mod.write_bytes(path, b"second", force=False)
            self.assertEqual(path.read_bytes(), b"first")
            self.mod.write_bytes(path, b"second", force=True)
            self.assertEqual(path.read_bytes(), b"second")

    def test_live_preflight_creates_output_directories_before_api_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "missing" / "nested" / "asset.png"
            self.mod.preflight_output_paths([output], force=False)
            self.assertTrue(output.parent.is_dir())

    def test_response_metadata_serializes_usage_and_returned_settings(self):
        usage = SimpleNamespace(model_dump=lambda **_: {"total_tokens": 42})
        response = SimpleNamespace(
            size="1536x1024",
            quality="high",
            background="opaque",
            output_format="png",
            usage=usage,
            _request_id="req_test",
        )
        data = self.mod.extract_response_metadata(response)
        self.assertEqual(data["usage"], {"total_tokens": 42})
        self.assertEqual(data["request_id"], "req_test")
        self.assertEqual(data["size"], "1536x1024")

    def test_response_metadata_accepts_stream_event_dicts(self):
        data = self.mod.extract_response_metadata(
            {
                "size": "1024x1024",
                "quality": "medium",
                "background": "transparent",
                "output_format": "png",
                "usage": {"total_tokens": 21},
            }
        )
        self.assertEqual(data["usage"], {"total_tokens": 21})
        self.assertEqual(data["background"], "transparent")

    def test_batch_loader_accepts_strings_and_objects_with_unique_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "jobs.jsonl"
            source.write_text(
                '"first prompt"\n'
                '{"prompt":"second prompt","model":"sunburst","quality":"high","out":"hero.png"}\n',
                encoding="utf-8",
            )
            jobs = self.mod.load_batch_jobs(source, root / "out")
            self.assertEqual(len(jobs), 2)
            self.assertEqual(jobs[0]["model"], "gpt-image-2.5-flare")
            self.assertEqual(jobs[1]["model"], "gpt-image-2.5-sunburst")
            self.assertNotEqual(jobs[0]["out"], jobs[1]["out"])

    def test_batch_loader_rejects_duplicate_output_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "jobs.jsonl"
            source.write_text(
                '{"prompt":"one","out":"same.png"}\n'
                '{"prompt":"two","out":"same.png"}\n',
                encoding="utf-8",
            )
            with self.assertRaises(self.mod.UsageError):
                self.mod.load_batch_jobs(source, root / "out")

    def test_batch_loader_rejects_cross_format_metadata_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "jobs.jsonl"
            source.write_text(
                '{"prompt":"one","output_format":"png","out":"same.png"}\n'
                '{"prompt":"two","output_format":"webp","out":"same.webp"}\n',
                encoding="utf-8",
            )
            with self.assertRaises(self.mod.UsageError):
                self.mod.load_batch_jobs(source, root / "out")

    def test_batch_loader_rejects_unknown_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "jobs.jsonl"
            source.write_text('{"prompt":"one","qualtiy":"high"}\n', encoding="utf-8")
            with self.assertRaises(self.mod.UsageError):
                self.mod.load_batch_jobs(source, root / "out")

    def test_batch_loader_rejects_non_integer_numeric_fields(self):
        cases = (
            ('{"prompt":"one","n":true}\n', "n"),
            ('{"prompt":"one","n":1.5}\n', "n"),
            (
                '{"prompt":"one","output_compression":true,"output_format":"webp"}\n',
                "output_compression",
            ),
            (
                '{"prompt":"one","output_compression":"70","output_format":"webp"}\n',
                "output_compression",
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "jobs.jsonl"
            for payload, field in cases:
                with self.subTest(field=field, payload=payload):
                    source.write_text(payload, encoding="utf-8")
                    with self.assertRaisesRegex(self.mod.UsageError, field):
                        self.mod.load_batch_jobs(source, root / "out")

    def test_retry_classification_is_bounded_to_transient_failures(self):
        transient = SimpleNamespace(status_code=429, code="rate_limit_exceeded")
        server = SimpleNamespace(status_code=503, code="internal_server_error")
        invalid = SimpleNamespace(status_code=400, code="image_generation_user_error")
        moderation = SimpleNamespace(status_code=400, code="moderation_blocked")
        quota = SimpleNamespace(status_code=429, code="insufficient_quota")
        self.assertTrue(self.mod.is_retryable_error(transient))
        self.assertTrue(self.mod.is_retryable_error(server))
        self.assertFalse(self.mod.is_retryable_error(invalid))
        self.assertFalse(self.mod.is_retryable_error(moderation))
        self.assertFalse(self.mod.is_retryable_error(quota))

    def test_dry_run_rejects_invalid_runtime_controls(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = self.mod.main(
                [
                    "generate",
                    "--prompt",
                    "x",
                    "--dry-run",
                    "--max-attempts",
                    "99",
                ]
            )
        self.assertEqual(result, 2)
        self.assertIn("max-attempts", stderr.getvalue())
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "jobs.jsonl"
            source.write_text('"one"\n', encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                result = self.mod.main(
                    [
                        "generate-batch",
                        "--input",
                        str(source),
                        "--dry-run",
                        "--concurrency",
                        "0",
                    ]
                )
            self.assertEqual(result, 2)
            self.assertIn("concurrency", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
