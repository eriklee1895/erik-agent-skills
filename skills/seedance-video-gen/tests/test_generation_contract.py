"""Offline request-contract tests. Run with the generator's uv environment."""
import argparse
import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/generate_seedance_video.py"
spec = importlib.util.spec_from_file_location("seedance", SCRIPT)
sd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd)
STANDARD = "doubao-seedance-2-5-260628"
FLASH = "doubao-seedance-2-5-flash-261115"


def single(**overrides):
    values = dict(model=STANDARD, prompt="海岸黄昏，镜头缓慢前推", prompt_file=None,
                  first_frame=None, last_frame=None, reference_image=[],
                  reference_video=[], reference_audio=[], duration=5, ratio="16:9",
                  resolution=None, draft=False, generate_audio=True, watermark=False,
                  return_last_frame=False, priority=None, enable_web_search=False)
    values.update(overrides)
    return sd.build_payload(argparse.Namespace(**values))


class GenerationContract(unittest.TestCase):
    def test_default_standard_in_both_builders(self):
        self.assertEqual(sd.DEFAULT_MODEL, STANDARD)
        for p in (single(), sd.build_payload_from_shot({"prompt": "海岸"}, {})):
            self.assertEqual((p["model"], p["resolution"], p["duration"]),
                             (STANDARD, "720p", 5))

    def test_batch_model_override(self):
        self.assertEqual(sd.build_payload_from_shot({"prompt": "海岸", "model": FLASH},
                                                  {"model": STANDARD})["model"], FLASH)
        self.assertEqual(sd.build_payload_from_shot({"prompt": "海岸"},
                                                  {"model": FLASH})["model"], FLASH)

    def test_duration_boundaries(self):
        for model in (STANDARD, FLASH):
            for duration in (-1, 4, 30):
                single(model=model, duration=duration)
            for duration in (0, 3, 31, 4.5, True, "5"):
                with self.subTest(model=model, duration=duration), self.assertRaises(SystemExit):
                    sd.build_payload_from_shot({"prompt": "海岸", "model": model,
                                                "duration": duration}, {})

    def test_preencoded_content_cannot_bypass_body_limit(self):
        content = [sd.build_content_item("image_url", "data:image/png;base64," + "A" * 200,
                                         "reference_image")]
        with patch.object(sd, "MAX_BODY_BYTES", 100), self.assertRaises(SystemExit):
            sd.check_total_body_size(content, 0)

    def test_cli_dry_run_without_credentials(self):
        with tempfile.TemporaryDirectory() as workdir:
            for model in (STANDARD, FLASH):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "create", "--dry-run", "--model", model,
                     "--prompt", "海岸", "--duration", "30"], cwd=workdir,
                    env={**os.environ, "ARK_API_KEY": ""}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual((payload["model"], payload["duration"]), (model, 30))

    def test_flash_30_seconds_and_mov(self):
        for builder in (lambda: single(model=FLASH, duration=30, output_format="mov"),
                        lambda: sd.build_payload_from_shot(
                            {"prompt": "海岸", "model": FLASH, "duration": 30,
                             "output_format": "mov"}, {})):
            p = builder()
            self.assertEqual((p["model"], p["resolution"], p["output_format"]),
                             (FLASH, "720p", "mov"))

    def test_resolution_boundaries(self):
        single(resolution="1080p")
        for model, resolution in ((FLASH, "1080p"), (FLASH, "4k"), (STANDARD, "4k")):
            with self.subTest(model=model, resolution=resolution), self.assertRaises(SystemExit):
                single(model=model, resolution=resolution)
            with self.assertRaises(SystemExit):
                sd.build_payload_from_shot({"prompt": "海岸", "model": model,
                                            "resolution": resolution}, {})

    def test_removed_models_rejected(self):
        for model in ("doubao-seedance-2-0-260128", "doubao-seedance-2-0-fast-260128",
                      "doubao-seedance-2-0-mini-260615"):
            with self.subTest(model=model), self.assertRaises(SystemExit):
                sd.build_payload_from_shot({"prompt": "海岸", "model": model}, {})

    def test_flash_media_limits_and_audio_only(self):
        def refs(kind, count):
            return [sd.build_content_item(kind + "_url", "https://example.com/ref", "reference_" + kind)
                    for _ in range(count)]
        sd.validate_mode_constraints(refs("image", 10) + refs("video", 5) + refs("audio", 5), FLASH)
        for kind, count in (("image", 11), ("video", 6), ("audio", 6)):
            with self.subTest(kind=kind), self.assertRaises(SystemExit):
                sd.validate_mode_constraints(refs(kind, count), FLASH)
        for model in (STANDARD, FLASH):
            single(model=model, reference_audio=["https://example.com/voice.wav"])
        sd.validate_mode_constraints(refs("image", 30) + refs("video", 10) + refs("audio", 10), STANDARD)
        with self.assertRaises(SystemExit):
            sd.validate_mode_constraints(refs("image", 31), STANDARD)

    def test_task_locks_for_both_models(self):
        for model in (STANDARD, FLASH):
            with self.subTest(model=model):
                single(model=model, first_frame="https://example.com/start.png", ratio="adaptive")
                with self.assertRaises(SystemExit):
                    single(model=model, first_frame="https://example.com/start.png")
                with self.assertRaises(SystemExit):
                    single(model=model, last_frame="https://example.com/end.png", ratio="adaptive")
                with self.assertRaises(SystemExit):
                    single(model=model, first_frame="https://example.com/start.png", ratio="adaptive",
                           reference_audio=["https://example.com/a.wav"])
                single(model=model, reference_video=["https://example.com/src.mov"],
                       omni_reference_task_type="edit", ratio="adaptive", duration=-1)
                with self.assertRaises(SystemExit):
                    single(model=model, reference_video=["https://example.com/src.mov"],
                           omni_reference_task_type="edit", ratio="adaptive", duration=8)
                with self.assertRaises(SystemExit):
                    single(model=model, omni_reference_task_type="extend", ratio="adaptive")

    def test_draft_only_standard(self):
        p = single(draft=True)
        self.assertEqual((p["draft"], p["resolution"]), (True, "480p"))
        with self.assertRaises(SystemExit):
            single(model=FLASH, draft=True)
        with self.assertRaises(SystemExit):
            sd.build_payload_from_shot({"prompt": "海岸", "model": FLASH, "draft": True}, {})
        with self.assertRaises(SystemExit):
            sd.build_promote_draft_payload("cgt-flash", model=FLASH)
        p = sd.build_promote_draft_payload("cgt-standard")
        self.assertEqual(set(p), {"model", "content", "resolution"})
        self.assertEqual(p["content"], [{"type": "draft_task", "draft_task": {"id": "cgt-standard"}}])

    def test_draft_validity_cutover(self):
        cutoff = 1793152800  # 2026-10-28 10:00 UTC+8
        self.assertEqual(sd.draft_validity_seconds(cutoff - 1), 7 * 86400)
        self.assertEqual(sd.draft_validity_seconds(cutoff), 14 * 86400)

    def test_web_search_and_priority_validation(self):
        for model in (STANDARD, FLASH):
            self.assertEqual(single(model=model, enable_web_search=True)["tools"], [{"type": "web_search"}])
            with self.assertRaises(SystemExit):
                single(model=model, enable_web_search=True, reference_audio=["https://example.com/a.wav"])
        for priority in (-1, 10):
            with self.assertRaises(SystemExit):
                single(priority=priority)


class DraftPromotionContract(unittest.IsolatedAsyncioTestCase):
    async def test_ten_day_new_draft_promotes_with_minimal_payload(self):
        now = sd.DRAFT_VALIDITY_CUTOVER + 11 * 86400
        source = dict(model=STANDARD, draft=True, status="succeeded", created_at=now - 10 * 86400)
        args = argparse.Namespace(task_id="cgt-source", dry_run=False, create_only=True,
                                  output_format=None, watermark=None, return_last_frame=False,
                                  priority=None)
        with patch.object(sd, "get_auth", return_value=("test-only", "https://example.com")), \
             patch.object(sd, "_get_task_async", AsyncMock(return_value=source)), \
             patch.object(sd, "_create_task_async", AsyncMock(return_value={"id": "cgt-final"})) as create, \
             patch.object(sd.time, "time", return_value=now), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(await sd.cmd_promote_draft_async(args), 0)
        payload = create.call_args.args[-1]
        self.assertEqual(payload, {"model": STANDARD, "resolution": "1080p",
                                   "content": [{"type": "draft_task", "draft_task": {"id": "cgt-source"}}]})

    async def test_expired_new_draft_does_not_submit(self):
        created_at = sd.DRAFT_VALIDITY_CUTOVER
        args = argparse.Namespace(task_id="cgt-source", dry_run=False)
        source = dict(model=STANDARD, draft=True, status="succeeded", created_at=created_at)
        with patch.object(sd, "get_auth", return_value=("test-only", "https://example.com")), \
             patch.object(sd, "_get_task_async", AsyncMock(return_value=source)), \
             patch.object(sd, "_create_task_async", AsyncMock()) as create, \
             patch.object(sd.time, "time", return_value=created_at + 14 * 86400):
            with self.assertRaisesRegex(SystemExit, "14 days"):
                await sd.cmd_promote_draft_async(args)
        create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
