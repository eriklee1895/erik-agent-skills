"""Offline CLI contract tests; no paid API or external network is used.

Run: python -m unittest discover -s skills/avatar-creator/tests -v
Requires Pillow and httpx; media integration tests also require ffmpeg.
"""

import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest

from PIL import Image, ImageDraw


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "animate_avatar.py"
PROMPT = (
    "角色非常灵动的挥挥手，傻傻的转一圈，然后凑到镜头上，再回去。\n"
    "整个过程种，镜头不允许有任何的 zoom 或者 move 等动作，镜头固定。"
    "角色一直都保持“运动”而非“静止”状态。"
)
FFMPEG = shutil.which("ffmpeg")


class FakeArk:
    """A local HTTP boundary that records real requests from the CLI."""

    def __init__(self, output_dir, video=b""):
        self.output_dir = output_dir
        self.video = video
        self.posts = []
        self.gets = []
        self.download_auth = []
        self.persisted_at_poll = []
        self.create_status = 200
        self.task_status = "succeeded"
        self.task_id = "offline-task-123"
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def respond(self, status, body, content_type="application/json"):
                if not isinstance(body, bytes):
                    body = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                owner.posts.append((self.path, json.loads(body), self.headers.get("Authorization")))
                if self.path != "/api/v3/contents/generations/tasks":
                    self.respond(404, {})
                elif owner.create_status == 200:
                    self.respond(200, {"id": owner.task_id})
                else:
                    self.respond(owner.create_status, {"error": {"message": "ambiguous create"}})

            def do_GET(self):
                if self.path == "/fixture.mp4":
                    owner.download_auth.append(self.headers.get("Authorization"))
                    self.respond(200, owner.video, "video/mp4")
                    return
                owner.gets.append(self.path)
                try:
                    manifest = json.loads((owner.output_dir / "manifest.json").read_text())
                except (OSError, ValueError):
                    manifest = {}
                owner.persisted_at_poll.append(manifest.get("task_id"))
                if self.path != f"/api/v3/contents/generations/tasks/{owner.task_id}":
                    self.respond(404, {})
                    return
                response = {"id": owner.task_id, "status": owner.task_status}
                if owner.task_status == "succeeded":
                    response["content"] = {"video_url": owner.origin + "/fixture.mp4"}
                elif owner.task_status == "failed":
                    response["error"] = {"code": "ContentRisk", "message": "offline task failed"}
                self.respond(200, response)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.origin = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class AvatarCliTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "standalone animate_avatar.py has not been implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / "avatar.png"
        picture = Image.new("RGB", (320, 320), "#eeeeff")
        draw = ImageDraw.Draw(picture)
        draw.ellipse((70, 40, 250, 250), fill="#ffcc66")
        draw.ellipse((115, 105, 135, 125), fill="black")
        draw.ellipse((190, 105, 210, 125), fill="black")
        picture.save(self.image)
        self.output = self.root / "output"

    def run_cli(self, *args, server=None, script=SCRIPT, no_tools=False):
        env = os.environ.copy()
        for key in tuple(env):
            if key.upper().endswith("_PROXY") or key in ("ARK_API_KEY", "ARK_BASE_URL"):
                env.pop(key, None)
        env["NO_PROXY"] = "127.0.0.1,localhost"
        if server:
            env["ARK_API_KEY"] = "offline-test-key"
            env["ARK_BASE_URL"] = server.origin + "/api/v3"
        if no_tools:
            env["PATH"] = str(self.root / "no-executables")
        result = subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            env=env, cwd=self.root, text=True, capture_output=True, timeout=40,
        )
        self.assertNotIn("offline-test-key", result.stdout + result.stderr)
        return result

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def new_run(self, server, *extra):
        return self.run_cli(
            "--image", self.image, "--out", self.output,
            "--poll-interval", "0.01", "--max-wait", "0.15", *extra, server=server,
        )

    def resume(self, server, *extra):
        return self.run_cli(
            "--resume", "--out", self.output,
            "--poll-interval", "0.01", "--max-wait", "0.15", *extra, server=server,
        )

    def test_standalone_dry_run_needs_no_key_or_ffmpeg_and_leaves_no_submission(self):
        isolated = self.root / "isolated-skill" / "scripts" / SCRIPT.name
        isolated.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, isolated)
        result = self.run_cli(
            "--image", self.image, "--out", self.output, "--dry-run",
            script=isolated, no_tools=True,
        )
        self.assert_success(result)
        self.assertNotIn("base64,", result.stdout + result.stderr)
        if self.output.exists():
            self.assertEqual(list(self.output.iterdir()), [], "dry run persisted run state")

    def test_invalid_image_is_rejected_before_submission(self):
        self.image.write_bytes(b"this is not an image")
        with FakeArk(self.output) as server:
            result = self.new_run(server)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(server.posts, [])
            self.assertEqual(server.gets, [])

    def test_fixed_preset_cannot_be_overridden_by_cli(self):
        for option, value in (("--prompt", "different"), ("--model", "other"), ("--duration", "2")):
            with self.subTest(option=option):
                result = self.run_cli(
                    "--image", self.image, "--out", self.output, "--dry-run", option, value,
                )
                self.assertNotEqual(result.returncode, 0)

    def test_polling_limits_must_be_finite(self):
        for option in ("--poll-interval", "--max-wait"):
            for value in ("nan", "inf"):
                with self.subTest(option=option, value=value):
                    result = self.run_cli(
                        "--image", self.image, "--out", self.output, "--dry-run", option, value,
                    )
                    self.assertNotEqual(result.returncode, 0)

    def test_missing_ffmpeg_prevents_paid_submission(self):
        with FakeArk(self.output) as server:
            result = self.run_cli(
                "--image", self.image, "--out", self.output, server=server, no_tools=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(server.posts, [])
            self.assertEqual(server.gets, [])

    def test_timeout_persists_id_before_poll_and_resume_never_submits_again(self):
        with FakeArk(self.output) as server:
            server.task_status = "running"
            first = self.new_run(server)
            self.assertNotEqual(first.returncode, 0)
            self.assertEqual(len(server.posts), 1)
            self.assertTrue(server.gets)
            self.assertTrue(all(value == server.task_id for value in server.persisted_at_poll))
            manifest = json.loads((self.output / "manifest.json").read_text())
            self.assertEqual(manifest["task_id"], server.task_id)
            second = self.resume(server)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(len(server.posts), 1)
            third = self.new_run(server)
            self.assertNotEqual(third.returncode, 0)
            self.assertEqual(len(server.posts), 1)

    def test_request_has_fixed_motion_and_identical_first_and_last_frames(self):
        with FakeArk(self.output) as server:
            server.task_status = "running"
            self.new_run(server)
            self.assertEqual(len(server.posts), 1)
            path, payload, auth = server.posts[0]
            self.assertEqual(path, "/api/v3/contents/generations/tasks")
            self.assertEqual(auth, "Bearer offline-test-key")
            for key, expected in {
                "model": "doubao-seedance-2-5-260628", "duration": 10,
                "resolution": "720p", "ratio": "adaptive",
                "generate_audio": False, "watermark": False,
            }.items():
                self.assertEqual(payload[key], expected, key)
            entries = payload["content"]
            self.assertEqual(len(entries), 3)
            self.assertEqual(entries[0], {"type": "text", "text": PROMPT})
            first, last = entries[1:]
            self.assertEqual(first["type"], "image_url")
            self.assertEqual(last["type"], "image_url")
            self.assertEqual(first["role"], "first_frame")
            self.assertEqual(last["role"], "last_frame")
            self.assertEqual(first["image_url"]["url"], last["image_url"]["url"])
            url = first["image_url"]["url"]
            self.assertTrue(url.startswith("data:image/png;base64,"))
            self.assertEqual(base64.b64decode(url.split(",", 1)[1]), self.image.read_bytes())

    def test_ambiguous_create_never_retries_or_resubmits_and_accepts_recovered_id(self):
        with FakeArk(self.output) as server:
            server.create_status = 500
            first = self.new_run(server)
            self.assertNotEqual(first.returncode, 0)
            self.assertEqual(len(server.posts), 1)
            self.assertNotEqual(self.resume(server).returncode, 0)
            self.assertNotEqual(self.new_run(server).returncode, 0)
            self.assertEqual(len(server.posts), 1)
            server.task_status = "running"
            recovered = self.resume(server, "--task-id", server.task_id)
            self.assertNotEqual(recovered.returncode, 0)
            self.assertTrue(server.gets)
            self.assertEqual(len(server.posts), 1)
            manifest = json.loads((self.output / "manifest.json").read_text())
            self.assertEqual(manifest["task_id"], server.task_id)

    def test_failed_task_resume_never_submits_again(self):
        with FakeArk(self.output) as server:
            server.task_status = "failed"
            self.assertNotEqual(self.new_run(server).returncode, 0)
            self.assertEqual(len(server.posts), 1)
            self.assertNotEqual(self.resume(server).returncode, 0)
            self.assertEqual(len(server.posts), 1)
            self.assertFalse((self.output / "avatar.gif").exists())

    @unittest.skipUnless(FFMPEG, "ffmpeg is required for media integration")
    def test_success_downloads_without_api_credentials_and_exports_looping_media(self):
        fixture = self.root / "fixture.mp4"
        subprocess.run(
            [FFMPEG, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
             "testsrc2=size=320x320:rate=10", "-t", "0.6", "-an", "-c:v", "libx264",
             "-pix_fmt", "yuv420p", "-y", str(fixture)],
            check=True, capture_output=True, timeout=20,
        )
        for resume_first in (False, True):
            with self.subTest(resume_first=resume_first):
                self.output = self.root / ("resumed-output" if resume_first else "fresh-output")
                with FakeArk(self.output, fixture.read_bytes()) as server:
                    if resume_first:
                        server.task_status = "running"
                        self.assertNotEqual(self.new_run(server).returncode, 0)
                        server.task_status = "succeeded"
                        self.assert_success(self.resume(server))
                    else:
                        self.assert_success(self.new_run(server))
                    self.assertEqual(len(server.posts), 1)
                    self.assertEqual(server.download_auth, [None])
                    self.assertEqual((self.output / "source.mp4").read_bytes(), fixture.read_bytes())
                    for name in ("manifest.json", "source.mp4", "avatar.mp4", "avatar.gif"):
                        self.assertGreater((self.output / name).stat().st_size, 0, name)
                    with Image.open(self.output / "avatar.gif") as gif:
                        self.assertEqual(gif.info.get("loop"), 0)
                        self.assertGreater(gif.n_frames, 1)
                    subprocess.run(
                        [FFMPEG, "-v", "error", "-i", str(self.output / "avatar.mp4"), "-f", "null", "-"],
                        check=True, capture_output=True, timeout=20,
                    )
                    # A downloaded source is enough to recover an interrupted local
                    # export, even when the API key is no longer available.
                    (self.output / "avatar.mp4").unlink()
                    (self.output / "avatar.gif").unlink()
                    previous_gets = list(server.gets)
                    self.assert_success(self.run_cli("--resume", "--out", self.output))
                    self.assertEqual(server.gets, previous_gets)
                    self.assertEqual(len(server.posts), 1)
                    self.assertEqual(server.download_auth, [None])
                    self.assertGreater((self.output / "avatar.mp4").stat().st_size, 0)
                    with Image.open(self.output / "avatar.gif") as gif:
                        self.assertGreater(gif.n_frames, 1)
                        self.assertEqual(gif.info.get("loop"), 0)


if __name__ == "__main__":
    unittest.main()
