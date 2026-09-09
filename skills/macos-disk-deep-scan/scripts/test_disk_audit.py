#!/usr/bin/env python3
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("disk_audit", Path(__file__).with_name("disk_audit.py"))
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def result(stdout=b"", status="complete", stderr=b""):
    return {"status": status, "returncode": 0 if status == "complete" else 1, "stdout": stdout, "stderr": stderr}


class DiskAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="disk-audit-test-")
        self.root = Path(self.temporary.name).resolve()
        self.addCleanup(self.temporary.cleanup)

    def file(self, relative, data=b"sample"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def scan(self, **kwargs):
        options = dict(root=str(self.root), home=str(self.root), max_entries=1000,
                       max_depth=30, seconds=5, top=20, excludes=set())
        options.update(kwargs)
        return audit.walk_root(**options)

    def test_plain_scan_preserves_files_and_reports_allocation(self):
        path = self.file("project/node_modules/package/index.js", b"x" * 9000)
        before = (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_ino)
        report = self.scan()
        row = next(r for r in report["rows"] if r["path"].endswith("node_modules"))
        self.assertEqual(report["status"], "complete")
        self.assertEqual(row["category"], "generated_output_candidate")
        self.assertGreaterEqual(row["allocated_bytes"], path.stat().st_blocks * 512)
        self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_ino))
        self.assertTrue(report["rows_are_overlapping"])

    def test_no_symlink_following(self):
        self.file("real/file")
        (self.root / "link").symlink_to(self.root / "real", target_is_directory=True)
        report = self.scan()
        self.assertEqual(report["skipped"]["symlink_not_followed"], 1)
        alias = self.scan(root=str(self.root / "link"))
        self.assertEqual(alias["status"], "partial")
        self.assertNotIn("root_total", alias)

    def test_ancestor_symlink_is_rejected(self):
        self.file("real/child/file")
        (self.root / "link").symlink_to(self.root / "real", target_is_directory=True)
        report = self.scan(root=str(self.root / "link/child"))
        self.assertEqual(report["status"], "partial")

    def test_hardlink_is_counted_once(self):
        p = self.file("one", b"x" * 9000)
        os.link(p, self.root / "two")
        report = self.scan()
        self.assertEqual(report["root_total"]["allocated_bytes"],
                         self.root.stat().st_blocks * 512 + p.stat().st_blocks * 512)
        self.assertEqual(report["skipped"]["hardlink_already_counted"], 1)

    def test_sparse_file_has_separate_logical_and_allocated_sizes(self):
        path = self.root / "Docker.raw"
        with path.open("wb") as stream:
            stream.seek(16 * 1024 * 1024)
            stream.write(b"x")
        row = next(r for r in self.scan()["rows"] if r["path"] == str(path))
        self.assertGreater(row["logical_bytes"], row["allocated_bytes"])
        self.assertEqual(row["category"], "unknown")

    def test_special_files_are_not_opened(self):
        os.mkfifo(self.root / "runtime.pipe")
        report = self.scan()
        self.assertEqual(report["skipped"]["special_file"], 1)

    def test_budgets_report_incomplete_not_zero(self):
        self.file("a/b/c")
        for options in ({"max_entries": 1}, {"max_depth": 1}, {"seconds": 0}):
            with self.subTest(options=options):
                report = self.scan(**options)
                self.assertEqual(report["status"], "partial")
                self.assertTrue(report["totals_are_partial"])
                self.assertGreater(report["error_count"], 0)

    def test_missing_and_permission_errors_are_explicit(self):
        report = self.scan(root=str(self.root / "missing"))
        self.assertEqual(report["status"], "partial")
        with mock.patch.object(audit.os, "scandir", side_effect=PermissionError(13, "denied")):
            report = self.scan()
        self.assertEqual(report["errors"][0]["errno"], 13)
        self.assertTrue(report["totals_are_partial"])

    def test_exclusion_and_filesystem_boundary(self):
        p = self.file("excluded/a")
        report = self.scan(excludes={str(p.parent)})
        self.assertEqual(report["skipped"]["excluded"], 1)
        actual = os.lstat
        def different_device(path):
            info = actual(path)
            if str(path) == str(p.parent):
                fields = list(info)
                fields[2] = info.st_dev + 1
                return os.stat_result(fields)
            return info
        with mock.patch.object(audit.os, "lstat", side_effect=different_device):
            report = self.scan()
        self.assertEqual(report["skipped"]["other_filesystem"], 1)

    def test_nested_roots_are_rejected(self):
        with self.assertRaises(ValueError):
            audit.validate_roots([str(self.root), str(self.root / "child")])
        self.assertEqual(audit.validate_roots([str(self.root)] * 2), [str(self.root)])

    def test_classification_does_not_trust_temp_or_project_names(self):
        for p in ("/private/tmp/example-build", "/projects/demo/dist", "/projects/demo/target"):
            self.assertEqual(audit.classify(p, "/home/test"), "unknown")
        self.file("rust/Cargo.toml")
        self.assertEqual(audit.classify(str(self.root / "rust/target"), str(self.root)), "generated_output_candidate")
        self.assertEqual(audit.classify("/home/test/.npm/_cacache", "/home/test"), "regenerable_cache_candidate")
        self.assertEqual(audit.classify("/home/test/.npm-global/lib/node_modules", "/home/test"), "preserve")
        self.assertEqual(audit.classify("/home/test/.local/share/tool/node_modules", "/home/test"), "preserve")
        self.assertEqual(audit.classify("/project/evidence/node_modules", "/home/test"), "preserve")
        self.assertEqual(audit.classify("/home/test/Library/Application Support/Chrome/Profile/WebStorage", "/home/test"), "application_data_review")
        self.assertEqual(audit.classify("/project/.git/objects", "/home/test"), "preserve")

    def test_global_node_installations_are_preserved(self):
        for path in ("/opt/homebrew/lib/node_modules", "/usr/local/lib/node_modules",
                     "/home/test/.nvm/versions/node/v22/lib/node_modules",
                     "/home/test/.volta/tools/image/node/22/lib/node_modules",
                     "/home/test/Library/Application Support/fnm/node-versions/v22/installation/lib/node_modules"):
            with self.subTest(path=path):
                self.assertEqual(audit.classify(path, "/home/test"), "preserve")

    def test_bounded_command_times_out_and_limits_output(self):
        start = time.monotonic()
        timed = audit.bounded_command([sys.executable, "-I", "-B", "-c", "import time; time.sleep(5)"], 0.1)
        self.assertEqual(timed["status"], "timeout")
        self.assertLess(time.monotonic() - start, 2)
        large = audit.bounded_command([sys.executable, "-I", "-B", "-c", "print('x'*20000)"], 2, 1000)
        self.assertEqual(large["status"], "output_limit")
        self.assertLessEqual(len(large["stdout"]) + len(large["stderr"]), 1000)

    def test_lsof_handles_spaces_and_newlines(self):
        path = "/projects/a space/line\nfeed"
        raw = b"p123\0cnode\0\nf10\0tREG\0n" + os.fsencode(path) + b"\0\n"
        parsed = audit.parse_lsof(raw)
        self.assertEqual(parsed[0]["path"], path)
        observed = audit.observe_activity(path, None, result(raw), result())
        self.assertEqual(observed["state"], "observed_active")

    def test_command_references_detect_loaded_npx_without_leaking_secrets(self):
        path = "/home/test/.npm/_npx/run"
        args = b"987654 node /home/test/.npm/_npx/run/mcp --token FAKE_SECRET_SENTINEL\n"
        observed = audit.observe_activity(path, None, result(), result(args))
        self.assertEqual(observed["state"], "observed_active")
        self.assertNotIn("FAKE_SECRET_SENTINEL", json.dumps(observed))
        self.assertEqual(observed["hits"], [{"pid": "987654", "kind": "command_path_reference"}])

    def test_repository_cwd_and_tmp_alias(self):
        raw = b"p123\0cnode\0fcwd\0tDIR\0n/tmp/repo\0\n"
        observed = audit.observe_activity("/private/tmp/repo/node_modules", "/private/tmp/repo", result(raw), result())
        self.assertEqual(observed["state"], "observed_active")

    def test_own_probe_does_not_make_repository_active(self):
        raw = f"p{os.getpid()}\0cpython\0fcwd\0tDIR\0n/project\0".encode()
        raw += b"p999999\0clsof\0fcwd\0tDIR\0n/project\0"
        files = {**result(raw), "probe_pid": 999999}
        observed = audit.observe_activity("/project/node_modules", "/project", files, result())
        self.assertEqual(observed["state"], "not_observed")
        files["stdout"] += b"p1234\0clsof\0fcwd\0tDIR\0n/project\0"
        observed = audit.observe_activity("/project/node_modules", "/project", files, result())
        self.assertEqual(observed["state"], "observed_active")

    def test_unix_socket_marks_directory_active(self):
        raw = b"p123\0cservice\0f9\0tunix\0n/private/tmp/runtime/service.sock\0"
        observed = audit.observe_activity("/private/tmp/runtime", None, result(raw), result())
        self.assertEqual(observed["state"], "observed_active")
        self.assertEqual(observed["hits"], [{"pid": "123", "kind": "open_file"}])

    def test_failed_or_partial_process_query_is_unknown(self):
        for status in ("timeout", "output_limit", "unavailable", "command_error"):
            with self.subTest(status=status):
                observed = audit.observe_activity("/cache", None, result(status=status), result())
                self.assertEqual(observed["state"], "unknown")
        observed = audit.observe_activity("/cache", None, result(), result())
        self.assertEqual(observed["state"], "not_observed")

    def test_dirty_repo_and_tracked_candidate_are_preserved(self):
        self.file("repo/source.txt")
        root = str(self.root / "repo")
        mocked = [result(os.fsencode(root) + b"\n"), result(status="command_error"),
                  result(b" M source.txt\0"), result(b"source.txt\0")]
        with mock.patch.object(audit, "git_command", side_effect=mocked):
            evidence, found = audit.git_evidence(root + "/source.txt", 1)
        self.assertEqual(found, root)
        self.assertEqual(evidence["state"], "dirty")
        self.assertTrue(evidence["tracked_under_candidate"])
        self.assertNotIn("source.txt", json.dumps(evidence))

    def test_configured_git_filters_skip_status(self):
        root = str(self.root)
        mocked = [result(os.fsencode(root) + b"\n"), result(b"filter.example.clean external-command\n")]
        with mock.patch.object(audit, "git_command", side_effect=mocked) as command:
            evidence, found = audit.git_evidence(root, 1)
        self.assertEqual(evidence["state"], "unknown_filter_configuration")
        self.assertEqual(command.call_count, 2)
        self.assertEqual(found, root)

    def test_process_visibility_warning_prevents_negative_claim(self):
        observed = audit.observe_activity("/cache", None, result(stderr=b"cannot stat filesystem"), result())
        self.assertEqual(observed["state"], "unknown")

    def test_preserve_category_survives_inspection(self):
        path = self.file("evidence/receipt")
        args = audit.parser().parse_args(["inspect", "--path", str(path)])
        with mock.patch.object(audit, "bounded_command", return_value=result()), \
             mock.patch.object(audit, "git_evidence", return_value=({"state": "unknown_or_not_repository"}, None)):
            report = audit.inspect_paths(args)
        self.assertEqual(report["paths"][0]["recommendation"], "preserve")

    def test_cli_has_no_cleanup_mode(self):
        for command in (["delete"], ["scan", "--delete"], ["scan", "--execute"]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                audit.parser().parse_args(command)
        for value in ("0", "-1", "nan", "inf"):
            with self.assertRaises(argparse.ArgumentTypeError):
                audit.positive_number(value)

    def test_worker_timeout_is_not_a_zero_byte_report(self):
        args = audit.parser().parse_args(["scan", "--root", str(self.root)])
        with mock.patch.object(audit, "bounded_command", return_value=result(status="timeout")):
            report = audit.scan(args)
        self.assertEqual(report["roots"][0]["status"], "timeout")
        self.assertNotIn("root_total", report["roots"][0])
        self.assertIsNone(report["reclaimable_bytes"])

    def test_top_rows_are_bounded(self):
        for i in range(10):
            self.file(f"p{i}/node_modules/index.js", b"x" * 100)
        report = self.scan(top=2)
        self.assertLessEqual(len(report["rows"]), 4)

    @unittest.skipUnless(sys.platform == "darwin", "macOS live CLI")
    def test_live_cli_read_only_fixture(self):
        path = self.file("project/node_modules/index.js")
        before = (path.read_bytes(), path.stat().st_mtime_ns)
        command = [sys.executable, "-I", "-B", str(Path(__file__).with_name("disk_audit.py")),
                   "scan", "--root", str(self.root), "--timeout", "5"]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(report["read_only"])
        self.assertEqual(report["roots"][0]["status"], "complete")
        self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))
        self.assertFalse(list(self.root.rglob("__pycache__")))


if __name__ == "__main__":
    unittest.main()
