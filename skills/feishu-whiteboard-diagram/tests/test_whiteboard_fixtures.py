import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "evals" / "fixtures" / "human-eval"
WHITEBOARD_CLI = "@larksuite/whiteboard-cli@0.2.13"
EXPECTED_WARNINGS = {
    "01-layered-strip.svg": 0,
    "02-task-loop.svg": 2,
    "03-learning-loop.svg": 18,
    "04-multicolumn-runtime.svg": 1,
    "05-recovery-layers.svg": 0,
    "09-comparison.svg": 0,
    "10-hub.svg": 1,
    "11-timeline.svg": 4,
    "12-swimlane.svg": 3,
    "13-quadrant.svg": 1,
    "14-focus-detail.svg": 1,
}


@unittest.skipUnless(shutil.which("npx"), "npx is required for fixture checks")
class WhiteboardFixtureTests(unittest.TestCase):
    def test_current_fixtures_have_no_errors_or_new_warnings(self):
        for name, expected_warnings in EXPECTED_WARNINGS.items():
            with self.subTest(name=name):
                completed = subprocess.run(
                    [
                        "npx",
                        "-y",
                        WHITEBOARD_CLI,
                        "-i",
                        str(FIXTURES / name),
                        "-f",
                        "svg",
                        "--check",
                    ],
                    text=True,
                    capture_output=True,
                    check=True,
                )
                payload = json.loads(completed.stdout)
                check = payload["data"]["check"]
                self.assertEqual(0, check["errors"], check["issues"])
                self.assertEqual(expected_warnings, check["warnings"], check["issues"])


if __name__ == "__main__":
    unittest.main()
