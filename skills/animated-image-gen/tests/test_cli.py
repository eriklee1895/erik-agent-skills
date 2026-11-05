import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/animated_image_gen.py"


class CLITests(unittest.TestCase):
    def run_cli(self, *arguments, cwd=None):
        environment = os.environ.copy()
        environment.pop("ARK_API_KEY", None)
        environment["PYTHONPATH"] = ""
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, arguments)], cwd=cwd, env=environment, capture_output=True, text=True)

    def test_dry_run_is_credential_free_and_produces_png_request(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("generate", "--prompt", "A fox blinks", "--transparent", "--dry-run", cwd=directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["format"], "webp")
        self.assertEqual(data["size"], [256, 256])
        self.assertEqual(data["payload"]["model"], "doubao-seedream-5-0-pro-260628")
        self.assertEqual(data["payload"]["output_format"], "png")
        self.assertNotIn("frame_count", data["payload"])

    def test_existing_job_is_protected_before_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            job = Path(directory) / "job"
            job.mkdir()
            (job / "keep.txt").write_text("keep")
            result = self.run_cli("generate", "--prompt", "A fox waves", "--out-dir", job, cwd=directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exists", result.stderr.lower())
            self.assertEqual((job / "keep.txt").read_text(), "keep")

    def test_unsupported_delivery_is_rejected(self):
        result = self.run_cli("generate", "--prompt", "test", "--format", "png", "--dry-run")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)

    def test_invalid_generation_options_fail_in_dry_run(self):
        for arguments in [("--poses", "0"), ("--duration", "-1"), ("--quality", "101"), ("--plays", "-1"), ("--cell-inset", "-2")]:
            with self.subTest(arguments=arguments):
                result = self.run_cli("generate", "--prompt", "A fox blinks", "--dry-run", *arguments)
                self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_single_pose_requires_master_route(self):
        result = self.run_cli("generate", "--prompt", "A fox blinks", "--poses", "1", "--dry-run")
        self.assertNotEqual(result.returncode, 0)
        master = self.run_cli("generate", "--prompt", "A fox", "--master-only", "--dry-run")
        self.assertEqual(master.returncode, 0, master.stderr)
        self.assertEqual(json.loads(master.stdout)["operation"], "master")

    def test_static_input_is_validated_before_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = self.run_cli("generate", "--prompt", "A fox blinks", "--motion-region", "0.2,0.2,0.3,0.3",
                                   "--static-image", str(Path(directory) / "missing.png"), "--dry-run", cwd=directory)
            self.assertNotEqual(missing.returncode, 0)
            wide = Path(directory) / "wide.png"
            Image.new("RGB", (200, 50)).save(wide)
            mismatch = self.run_cli("generate", "--prompt", "A fox blinks", "--motion-region", "0.2,0.2,0.3,0.3",
                                    "--static-image", wide, "--dry-run", cwd=directory)
            self.assertNotEqual(mismatch.returncode, 0)

    def test_pixel_template_applies_finishing_defaults(self):
        result = self.run_cli("generate", "--template", "pixel-flame", "--set", "effect=small flame", "--set", "palette=orange and yellow", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan.get("resample"), "nearest")
        self.assertEqual(plan.get("colors"), 64)

    def test_encode_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frames = root / "frames"
            frames.mkdir()
            for index, x in enumerate([2, 12, 22]):
                image = Image.new("RGBA", (40, 40))
                ImageDraw.Draw(image).ellipse((x, 10, x + 12, 22), fill="orange")
                image.save(frames / f"frame-{index:02d}.png")
            target = root / "output.webp"
            result = self.run_cli("encode", "--input", frames, "--out", target, "--duration", "0.9", cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            meta = json.loads(result.stdout)
            self.assertEqual(meta["cycle_ms"], 900)
            self.assertEqual(meta["size"], [40, 40])

    def test_local_contact_sheet_does_not_overwrite_user_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frames = root / "frames"
            frames.mkdir()
            for index, x in enumerate([2, 12]):
                image = Image.new("RGBA", (40, 40))
                ImageDraw.Draw(image).ellipse((x, 10, x + 12, 22), fill="orange")
                image.save(frames / f"frame-{index:02d}.png")
            existing = root / "contact.jpg"
            existing.write_bytes(b"preserve")
            result = self.run_cli("encode", "--input", frames, "--out", root / "output.webp", "--size", "80x80", cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(existing.read_bytes(), b"preserve")
            self.assertTrue(Path(json.loads(result.stdout)["contact_sheet"]).is_file())


if __name__ == "__main__":
    unittest.main()
