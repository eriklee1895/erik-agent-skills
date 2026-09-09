#!/usr/bin/env python3
import argparse
import datetime
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
import time

GENERATED = {"node_modules", ".next", ".turbo", ".venv", "__pycache__", ".build", ".derivedData", "DerivedData"}
CACHE_PATHS = (
    ".npm/_cacache", ".npm/_npx", ".cache/uv", ".cache/pip",
    "Library/pnpm/store", "Library/Caches/Homebrew", "Library/Caches/go-build",
    "Library/Caches/org.swift.swiftpm", "Library/Caches/pip", "go/pkg/mod",
    ".cargo/registry", ".cargo/git", ".gradle/caches", ".m2/repository",
)
PROTECTED_PARTS = {".git", "Keychains", "Mobile Documents", "CloudStorage", "Photos Library.photoslibrary"}
DEFAULT_EXCLUDES = {"/dev", "/Volumes", "/Network", "/System", "/private/var/vm"}


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def absolute(path):
    return os.path.abspath(os.path.expanduser(path))


def within(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


def identity(info):
    return {"device": info.st_dev, "inode": info.st_ino, "mtime_ns": info.st_mtime_ns,
            "owner_uid": info.st_uid, "mode": stat.S_IMODE(info.st_mode)}


def classify(path, home):
    parts = Path(path).parts
    name = os.path.basename(path)
    if PROTECTED_PARTS.intersection(parts) or any(within(path, p) for p in ("/System", "/private/var/vm")):
        return "preserve"
    if any(within(path, p) for p in ("/Applications", "/opt/homebrew/Cellar", "/opt/homebrew/lib/node_modules",
                                    "/usr/local/lib/node_modules")):
        return "preserve"
    if any(within(path, os.path.join(home, p)) for p in (
        ".npm-global", ".bun/install/global", "Library/pnpm/global", ".local/share",
        ".nvm", ".fnm", ".volta", ".nodenv", ".asdf", "Library/Application Support/fnm",
    )) or any(p in parts for p in ("sessions", "archived_sessions", "backups", "evidence", "vm_bundles")):
        return "preserve"
    if any(within(path, os.path.join(home, p)) for p in CACHE_PATHS):
        return "regenerable_cache_candidate"
    if any(p in parts for p in ("WebStorage", "CacheStorage", "Service Worker", "IndexedDB", "Local Storage")):
        return "application_data_review"
    if name in GENERATED:
        return "generated_output_candidate"
    if name == "target" and os.path.isfile(os.path.join(os.path.dirname(path), "Cargo.toml")):
        return "generated_output_candidate"
    if name in {"CachedData", "CachedExtensionVSIXs", "GPUCache", "Code Cache"}:
        return "regenerable_cache_candidate"
    if name in {"logs", "log", "update", "update_downloading", "OptGuideOnDeviceModel"}:
        return "application_data_review"
    if name in {".worktrees", "worktrees"}:
        return "worktree_review"
    return "unknown"


def bounded_command(argv, timeout=15, max_bytes=1024 * 1024, env=None):
    started = time.monotonic()
    output = {"stdout": bytearray(), "stderr": bytearray()}
    reason = None
    try:
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    except OSError as exc:
        return {"status": "unavailable", "returncode": None, "stdout": b"", "stderr": b"", "errno": exc.errno}
    with selectors.DefaultSelector() as selector:
        for label, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map():
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                reason = "timeout"
                break
            for key, _ in selector.select(min(remaining, 0.1)):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                available = max_bytes - sum(len(v) for v in output.values())
                output[key.data].extend(chunk[:available])
                if len(chunk) > available:
                    reason = "output_limit"
                    break
            if reason:
                break
    if reason and process.poll() is None:
        process.kill()
    try:
        code = process.wait(timeout=max(0.1, timeout - (time.monotonic() - started)))
    except subprocess.TimeoutExpired:
        process.kill()
        code = process.wait()
        reason = reason or "timeout"
    finally:
        process.stdout.close()
        process.stderr.close()
    return {"status": reason or ("complete" if code == 0 else "command_error"),
            "returncode": code, "probe_pid": process.pid, **{k: bytes(v) for k, v in output.items()}}


def command_summary(result):
    return {k: v for k, v in result.items() if k not in ("stdout", "stderr")}


def walk_root(root, home, max_entries, max_depth, seconds, top, excludes):
    start = time.monotonic()
    report = {"root": root, "status": "complete", "entries_seen": 0, "errors": [],
              "error_count": 0, "skipped": {}, "rows": [], "captured_at": timestamp()}
    hardlinks = set()
    candidates = []
    boundaries = []
    ranking_counts = {"immediate_children": 0, "candidates": 0}
    stop = False

    def issue(path, reason, error=None):
        report["status"] = "partial"
        report["error_count"] += 1
        if len(report["errors"]) < 20:
            report["errors"].append({"path": path, "reason": reason, "errno": error})

    def skip(reason):
        report["skipped"][reason] = report["skipped"].get(reason, 0) + 1

    def row(path, size, logical, info):
        return {"path": path, "allocated_bytes": size, "logical_bytes": logical,
                "category": classify(path, home), "identity": identity(info)}

    def visit(path, depth, device, inside_candidate=False):
        nonlocal stop
        if stop:
            return 0, 0
        if report["entries_seen"] >= max_entries or time.monotonic() - start >= seconds:
            stop = True
            issue(path, "entry_or_time_budget")
            return 0, 0
        report["entries_seen"] += 1
        try:
            info = os.lstat(path)
        except OSError as exc:
            issue(path, "inaccessible_or_changed", exc.errno)
            return 0, 0
        if stat.S_ISLNK(info.st_mode):
            skip("symlink_not_followed")
            return 0, 0
        if info.st_dev != device:
            skip("other_filesystem")
            issue(path, "other_filesystem_not_scanned")
            return 0, 0
        if any(within(path, x) for x in excludes):
            skip("excluded")
            issue(path, "excluded")
            return 0, 0
        if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            skip("special_file")
            return 0, 0
        if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
            key = (info.st_dev, info.st_ino)
            if key in hardlinks:
                skip("hardlink_already_counted")
                return 0, 0
            hardlinks.add(key)
        size, logical = info.st_blocks * 512, info.st_size
        candidate = classify(path, home) in {"regenerable_cache_candidate", "generated_output_candidate"}
        if stat.S_ISDIR(info.st_mode):
            if depth >= max_depth:
                issue(path, "depth_budget")
            else:
                try:
                    with os.scandir(path) as entries:
                        for entry in entries:
                            a, b = visit(entry.path, depth + 1, device, inside_candidate or candidate)
                            size += a
                            logical += b
                            if stop:
                                break
                except OSError as exc:
                    issue(path, "inaccessible_or_changed", exc.errno)
        item = row(path, size, logical, info)
        if depth == 1:
            ranking_counts["immediate_children"] += 1
            boundaries.append(item)
            boundaries.sort(key=lambda r: r["allocated_bytes"], reverse=True)
            del boundaries[top:]
        if candidate and not inside_candidate:
            ranking_counts["candidates"] += 1
            candidates.append(item)
            candidates.sort(key=lambda r: r["allocated_bytes"], reverse=True)
            del candidates[top:]
        return size, logical

    try:
        info = os.lstat(root)
        if os.path.realpath(root) != root or stat.S_ISLNK(info.st_mode):
            issue(root, "symlink_or_alias_root_use_explicit_canonical_path")
        else:
            size, logical = visit(root, 0, info.st_dev)
            report["root_total"] = row(root, size, logical, info)
    except OSError as exc:
        issue(root, "inaccessible_or_missing", exc.errno)
    merged = {r["path"]: r for r in boundaries + candidates}
    report["rows"] = sorted(merged.values(), key=lambda r: r["allocated_bytes"], reverse=True)
    report["ranking_counts"] = ranking_counts
    report["rankings_truncated"] = any(n > top for n in ranking_counts.values())
    report["rows_are_overlapping"] = True
    report["totals_are_partial"] = report["status"] != "complete"
    report["elapsed_seconds"] = round(time.monotonic() - start, 3)
    return report


def developer_roots(home):
    return [os.path.join(home, p) for p in CACHE_PATHS] + [
        os.path.join(home, "Library/Developer/Xcode/DerivedData")]


def validate_roots(roots):
    roots = list(dict.fromkeys(absolute(p) for p in roots))
    for i, root in enumerate(roots):
        for other in roots[i + 1:]:
            if within(root, other) or within(other, root):
                raise ValueError(f"Overlapping roots: {root!r}, {other!r}; scan separately, do not add their totals.")
    return roots


def scan(args):
    home = absolute(str(Path.home()))
    roots = args.root + (developer_roots(home) if args.preset == "developer" else [])
    if not roots:
        raise ValueError("Provide --root or --preset developer; no implicit whole-disk traversal.")
    roots = validate_roots(roots)
    if len(roots) > 40:
        raise ValueError("At most 40 roots per invocation.")
    deadline = time.monotonic() + args.budget_seconds
    results = []
    for root in roots:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            results.append({"root": root, "status": "not_scanned_budget"})
            continue
        seconds = min(args.timeout, remaining)
        command = [sys.executable, "-I", "-B", os.path.abspath(__file__), "_walk", "--root", root,
                   "--home", home, "--max-entries", str(args.max_entries), "--max-depth", str(args.max_depth),
                   "--seconds", str(seconds), "--top", str(args.top)]
        for excluded in args.exclude:
            command.extend(["--exclude", absolute(excluded)])
        result = bounded_command(command, seconds, 4 * 1024 * 1024)
        if result["status"] == "complete":
            try:
                results.append(json.loads(result["stdout"]))
            except (ValueError, UnicodeError):
                results.append({"root": root, "status": "invalid_worker_output"})
        else:
            results.append({"root": root, **command_summary(result), "totals_are_partial": True})
    return {"mode": "scan", "roots": results, "reclaimable_bytes": None,
            "limits": {"per_root_seconds": args.timeout, "total_seconds": args.budget_seconds,
                       "entries_per_root": args.max_entries, "depth": args.max_depth},
            "notes": ["Allocated bytes are not guaranteed reclaimable bytes; APFS clones may share extents.",
                      "Nested rows overlap. Hardlinks are deduplicated within each root only; do not sum roots blindly.",
                      "Traversal is not an atomic snapshot; paths and usage may change. Activity is not checked by scan."]}


def parse_lsof(raw):
    records = []
    pid = command = fd = kind = ""
    for field in raw.split(b"\0"):
        field = field.lstrip(b"\n")
        if not field:
            continue
        tag, value = field[:1], os.fsdecode(field[1:])
        if tag == b"p":
            pid, command, fd, kind = value, "", "", ""
        elif tag == b"c":
            command = value
        elif tag == b"f":
            fd, kind = value, ""
        elif tag == b"t":
            kind = value
        elif tag == b"n" and kind in ("REG", "DIR", "unix"):
            records.append({"pid": pid, "command": command, "fd": fd, "path": value, "type": kind})
    return records


def system_alias(path):
    for alias in ("/tmp", "/var", "/etc"):
        if within(path, alias):
            return "/private" + path
    return path


def observe_activity(path, repository, files_result, args_result):
    hits = []
    for record in parse_lsof(files_result["stdout"]):
        if record["pid"] in {str(os.getpid()), str(files_result.get("probe_pid"))}:
            continue
        observed = system_alias(record["path"])
        cwd = record["fd"] == "cwd" and repository and within(observed, repository)
        if within(observed, path) or cwd:
            hits.append({"pid": record["pid"], "kind": "repository_cwd" if cwd else "open_file"})
    aliases = {path}
    if path.startswith("/private/"):
        aliases.add(path[len("/private"):])
    if repository:
        aliases.add(repository)
    for line in args_result["stdout"].splitlines():
        fields = line.split(None, 1)
        if len(fields) != 2 or not fields[0].isdigit() or int(fields[0]) in (os.getpid(), os.getppid()):
            continue
        if any(os.fsencode(p) in fields[1] for p in aliases):
            hits.append({"pid": fields[0].decode("ascii"), "kind": "command_path_reference"})
    hits = list({(h["pid"], h["kind"]): h for h in hits}.values())
    complete = all(r["status"] == "complete" and not r["stderr"] for r in (files_result, args_result)) and "\n" not in path
    return {"state": "observed_active" if hits else ("not_observed" if complete else "unknown"),
            "hits": hits[:30], "hit_count": len(hits), "collection_complete": complete,
            "lsof": command_summary(files_result), "processes": command_summary(args_result),
            "limitation": "Current-user visibility and one moment only; not_observed is not proof of inactivity."}


def git_command(directory, arguments, timeout):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return bounded_command(["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                            "-c", "core.untrackedCache=false", "-c", "core.hooksPath=/dev/null",
                            "-C", directory, *arguments], timeout, 2 * 1024 * 1024, env)


def git_evidence(path, timeout):
    directory = path if os.path.isdir(path) else os.path.dirname(path)
    found = git_command(directory, ["rev-parse", "--show-toplevel"], timeout)
    if found["status"] != "complete":
        return {"state": "unknown_or_not_repository", "probe": command_summary(found)}, None
    root = os.fsdecode(found["stdout"]).rstrip("\n")
    if not os.path.isabs(root) or not within(path, root):
        return {"state": "unknown_repository_path"}, None
    filters = git_command(root, ["config", "--get-regexp", r"^filter\..*\.(clean|process)$"], timeout)
    if filters["status"] != "command_error" or filters["returncode"] != 1 or filters["stderr"]:
        return {"root": root, "state": "unknown_filter_configuration",
                "limitation": "Skip status rather than execute repository clean/process filters."}, root
    changed = git_command(root, ["status", "--porcelain=v1", "-z", "--untracked-files=normal", "--ignore-submodules=all"], timeout)
    tracked = git_command(root, ["ls-files", "-z", "--", ":(literal)" + os.path.relpath(path, root)], timeout)
    known = all(r["status"] == "complete" for r in (changed, tracked))
    return {"root": root, "state": ("dirty" if changed["stdout"] else "clean") if known else "unknown",
            "tracked_under_candidate": bool(tracked["stdout"]) if tracked["status"] == "complete" else None,
            "status_probe": command_summary(changed), "tracked_probe": command_summary(tracked),
            "limitations": "Submodules are not inspected. Clean does not prove commits are merged, ignored data is disposable, or a worktree is unused."}, root


def inspect_paths(args):
    paths = list(dict.fromkeys(absolute(p) for p in args.path))
    if len(paths) > 20:
        raise ValueError("Inspect at most 20 exact paths per invocation.")
    files = bounded_command(["/usr/sbin/lsof", "-nP", "-F0pcftn"], args.timeout, 16 * 1024 * 1024)
    processes = bounded_command(["/bin/ps", "-axo", "pid=,args="], args.timeout, 8 * 1024 * 1024)
    results = []
    for path in paths:
        category = classify(path, str(Path.home()))
        item = {"path": path, "category": category,
                "recommendation": "preserve" if category == "preserve" else "review_only"}
        try:
            before = os.lstat(path)
            item["identity"] = identity(before)
            if os.path.realpath(path) != path or stat.S_ISLNK(before.st_mode):
                item["status"] = "symlink_or_alias_not_inspected"
                item["recommendation"] = "preserve"
            elif not (stat.S_ISDIR(before.st_mode) or stat.S_ISREG(before.st_mode)):
                item["status"] = "special_file_preserve"
                item["recommendation"] = "preserve"
            else:
                git, root = git_evidence(path, args.timeout)
                item["git"] = git
                item["activity"] = observe_activity(path, root, files, processes)
                item["status"] = "observed"
                if identity(os.lstat(path)) != identity(before):
                    item["status"] = "changed_during_inspection"
                if item["activity"]["state"] == "observed_active" or git.get("tracked_under_candidate"):
                    item["recommendation"] = "preserve"
        except OSError as exc:
            item.update(status="inaccessible_or_missing", errno=exc.errno)
        results.append(item)
    return {"mode": "inspect", "paths": results, "captured_at": timestamp(),
            "authorization": "none; observations are not deletion permissions or an execution manifest",
            "notes": ["No full command lines, environment values, file contents, or Git filenames are returned.",
                      "File identity is observational, not a content seal or protection against later path changes."]}


def overview(args):
    commands = {"filesystems": ["/bin/df", "-k"], "apfs": ["/usr/sbin/diskutil", "apfs", "list"],
                "snapshots": ["/usr/bin/tmutil", "listlocalsnapshots", "/"],
                "swap": ["/usr/sbin/sysctl", "vm.swapusage"]}
    results = {}
    for name, command in commands.items():
        result = bounded_command(command, args.timeout, 256 * 1024)
        results[name] = {**command_summary(result), "output": result["stdout"].decode("utf-8", "replace")}
    return {"mode": "overview", "observations": results, "captured_at": timestamp(),
            "notes": ["APFS volumes share container free space; never sum their free-space columns.",
                      "Do not delete swap, system snapshots, or Preboot to make the numbers smaller."]}


def positive_number(value):
    parsed = float(value)
    if not 0 < parsed <= 3600:
        raise argparse.ArgumentTypeError("Expected a finite value greater than 0 and at most 3600.")
    return parsed


def positive_int(value):
    parsed = int(value)
    if not 1 <= parsed <= 2000000:
        raise argparse.ArgumentTypeError("Expected an integer between 1 and 2000000.")
    return parsed


def parser():
    cli = argparse.ArgumentParser(description="Explicit, read-only macOS developer disk audit. JSON to stdout; no deletion mode.")
    commands = cli.add_subparsers(dest="mode", required=True)
    initial = commands.add_parser("overview", help="Read APFS, filesystem, snapshot, and swap summaries.")
    initial.add_argument("--timeout", type=positive_number, default=10)
    survey = commands.add_parser("scan", help="Measure explicit roots or known developer cache locations.")
    survey.add_argument("--root", action="append", default=[])
    survey.add_argument("--preset", choices=["developer"])
    survey.add_argument("--exclude", action="append", default=[])
    survey.add_argument("--timeout", type=positive_number, default=20)
    survey.add_argument("--budget-seconds", type=positive_number, default=120)
    survey.add_argument("--max-entries", type=positive_int, default=200000)
    survey.add_argument("--max-depth", type=positive_int, default=40)
    survey.add_argument("--top", type=positive_int, default=20)
    check = commands.add_parser("inspect", help="Inspect exact path identity, process references, and Git protection.")
    check.add_argument("--path", action="append", required=True)
    check.add_argument("--timeout", type=positive_number, default=15)
    worker = commands.add_parser("_walk", help=argparse.SUPPRESS)
    worker.add_argument("--root", required=True)
    worker.add_argument("--home", required=True)
    worker.add_argument("--max-entries", type=positive_int, required=True)
    worker.add_argument("--max-depth", type=positive_int, required=True)
    worker.add_argument("--seconds", type=positive_number, required=True)
    worker.add_argument("--top", type=positive_int, required=True)
    worker.add_argument("--exclude", action="append", default=[])
    return cli


def main():
    cli = parser()
    args = cli.parse_args()
    if sys.platform != "darwin":
        cli.error("Live audits support macOS only; no permission changes or dependencies will be installed.")
    if getattr(args, "max_depth", 1) > 80 or getattr(args, "top", 1) > 100:
        cli.error("--max-depth must be at most 80; --top must be at most 100.")
    try:
        if args.mode == "_walk":
            result = walk_root(args.root, args.home, args.max_entries, args.max_depth,
                               args.seconds * 0.85, args.top, DEFAULT_EXCLUDES | set(args.exclude))
        else:
            result = {"schema_version": 1, "read_only": True,
                      **{"overview": overview, "scan": scan, "inspect": inspect_paths}[args.mode](args)}
    except ValueError as exc:
        cli.error(str(exc))
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if args.mode == "scan" and any(r["status"] != "complete" for r in result["roots"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
