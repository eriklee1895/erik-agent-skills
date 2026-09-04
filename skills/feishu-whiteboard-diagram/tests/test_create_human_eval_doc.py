import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "evals" / "create_human_eval_doc.sh"


FAKE_LARK_CLI = r"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$FAKE_LARK_LOG"

if [ "${1:-}" = "auth" ]; then
  printf '%s\n' '{"ok":true,"data":{"verified":true}}'
  exit 0
fi

if [ "${1:-}" = "docs" ] && [ "${2:-}" = "+script" ]; then
  printf '%s\n' '{"ok":true,"data":{"assessment":{"status":"pass"}}}'
  exit 0
fi

if [ "${1:-}" = "docs" ] && [ "${2:-}" = "+create" ]; then
  if [[ " $* " != *" --yes "* ]]; then
    printf '%s\n' '{"ok":false,"error":{"type":"confirmation","subtype":"confirmation_required","risk":"high-risk-write","action":"docs +create","hint":"add --yes to confirm"}}' >&2
    exit 10
  fi
  printf '%s\n' '{"ok":true,"data":{"document":{"url":"https://example.test/docx/abc","document_id":"abc","new_blocks":[]}}}'
  exit 0
fi

if [ "${1:-}" = "docs" ] && [ "${2:-}" = "+fetch" ]; then
  printf '%s\n' '{"ok":true,"data":{"document":{"content":"<whiteboard token=\"wbcn-1\"/><whiteboard token=\"wbcn-2\"/><whiteboard token=\"wbcn-3\"/><whiteboard token=\"wbcn-4\"/><whiteboard token=\"wbcn-5\"/><whiteboard token=\"wbcn-6\"/><whiteboard token=\"wbcn-7\"/><whiteboard token=\"wbcn-8\"/><whiteboard token=\"wbcn-9\"/>"}}}'
  exit 0
fi

if [ "${1:-}" = "whiteboard" ] && [ "${2:-}" = "+export" ]; then
  exit 0
fi

printf '%s\n' "unexpected fake command: $*" >&2
exit 99
"""


class CreateHumanEvalDocTests(unittest.TestCase):
    def run_script(
        self, *args: str
    ) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "lark-cli"
            fake.write_text(textwrap.dedent(FAKE_LARK_CLI), encoding="utf-8")
            fake.chmod(0o755)
            log = root / "calls.log"
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["FAKE_LARK_LOG"] = str(log)
            env["TMPDIR"] = str(root)
            completed = subprocess.run(
                ["bash", str(SCRIPT), *args],
                cwd=SCRIPT.parents[3],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            calls = log.read_text(encoding="utf-8").splitlines()
            return completed, calls

    def test_confirmation_required_is_returned_without_retry(self):
        completed, calls = self.run_script()
        creates = [call for call in calls if call.startswith("docs +create")]
        self.assertEqual(10, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual(1, len(creates), calls)
        self.assertNotIn("--yes", creates[0])

    def test_explicit_yes_is_forwarded_once(self):
        completed, calls = self.run_script("--yes")
        creates = [call for call in calls if call.startswith("docs +create")]
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual(1, len(creates), calls)
        self.assertIn("--yes", creates[0])

    def test_explicit_yes_exports_every_board_for_review(self):
        completed, calls = self.run_script("--yes")
        exports = [call for call in calls if call.startswith("whiteboard +export")]
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual(9, len(exports), calls)


if __name__ == "__main__":
    unittest.main()
