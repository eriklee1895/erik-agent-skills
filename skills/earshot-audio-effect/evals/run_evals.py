#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Artifact evals for the real Earshot wrapper. No model or paid API is used."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "earshot_sfx.py"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def pcm(path):
    with wave.open(str(path)) as f:
        sr, frames, channels, width = (
            f.getframerate(),
            f.getnframes(),
            f.getnchannels(),
            f.getsampwidth(),
        )
        raw = f.readframes(frames)
    require(width == 3, "expected PCM_24 WAV")
    samples = [
        int.from_bytes(raw[i : i + 3], "little", signed=True) / 8388608
        for i in range(0, len(raw), 3)
    ]
    mono = [
        sum(samples[i : i + channels]) / channels
        for i in range(0, len(samples), channels)
    ]
    require(
        frames > 1 and max(map(abs, samples)) > 0, "audio must be nonempty and audible"
    )
    # -1.0 is a legal PCM endpoint; one full-scale sample does not prove clipping.
    require(max(map(abs, samples)) <= 1, "PCM must not be over full scale")
    # Independent calculation from delivered bytes; does not call Earshot's timing helper.
    prefix = [0.0]
    for sample in mono:
        prefix.append(prefix[-1] + sample * sample)
    window, hop = max(1, sr // 200), max(1, sr // 1000)
    starts = range(0, max(1, frames - window + 1), hop)
    start = max(
        starts,
        key=lambda i: (
            (prefix[min(i + window, frames)] - prefix[i]) / min(window, frames - i)
        ),
    )
    return {
        "sr": sr,
        "frames": frames,
        "channels": channels,
        "duration_s": frames / sr,
        "peak_s": (start + window / 2) / sr,
        "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
    }


class Runner:
    def __init__(self, out, offline=False, jobs=2):
        self.out = out
        self.offline = offline
        self.case_dir = out
        self.command_no = 0
        self.jobs = jobs

    def call(self, *args, fail=False):
        command = ["uv", "run", "--locked"]
        if self.offline:
            command.append("--offline")
        command += ["--script", str(SCRIPT), *map(str, args)]
        p = subprocess.run(
            command,
            cwd=self.case_dir,
            text=True,
            capture_output=True,
            timeout=240,
            check=False,
        )
        self.command_no += 1
        prefix = self.case_dir / f"command-{self.command_no}"
        prefix.with_suffix(".json").write_text(p.stdout, encoding="utf-8")
        prefix.with_suffix(".log").write_text(p.stderr, encoding="utf-8")
        require(
            (p.returncode != 0) if fail else (p.returncode == 0), p.stderr + p.stdout
        )
        result = json.loads(p.stdout)
        require(result["ok"] == (not fail), "unexpected command completion status")
        return result

    def render(self, name, *args):
        return self.call(
            "render",
            "whoosh_fast/crisp",
            "--dur",
            "0.8",
            "--apex",
            "0.32",
            "--seed",
            "42",
            "--out",
            self.case_dir / name,
            *args,
        )

    def case(self, name):
        self.case_dir = self.out / name
        self.case_dir.mkdir(parents=True, exist_ok=True)
        self.command_no = 0
        fn = getattr(self, name.replace("-", "_"))
        return fn()

    def lightweight_runtime(self):
        r = self.call("doctor")["runtime"]
        require(r["earshot"] == "0.3.0", "incorrect source version")
        require(
            not r["forbidden_packages"] and not r["forbidden_modules_loaded"],
            "heavy dependencies found",
        )
        return r

    def dynamic_catalog(self):
        full = self.call("list")["sounds"]
        require(len(full) == 201, "pinned bank count changed")
        rows = self.call("list", "--category", "whoosh_fast")["sounds"]
        require(
            rows and all(r["category"] == "whoosh_fast" for r in rows),
            "bad category filter",
        )
        require(all("knobs" in r for r in rows), "missing supported knob description")
        return {"count": len(full), "whoosh_fast_ids": [r["id"] for r in rows]}

    def whoosh_alignment(self):
        r = self.render("whoosh.wav", "--align", "peak", "--cue-at", "3")
        actual = pcm(r["audio"]["file"])
        require(
            actual["frames"] == 38400 and actual["sr"] == 48000,
            "incorrect length/sample rate",
        )
        require(abs(actual["peak_s"] - 0.32) <= 0.005, "peak missed target")
        require(
            abs(actual["peak_s"] - r["audio"]["peak_s"]) < 0.0001,
            "metadata does not describe PCM",
        )
        require(
            abs(r["placement"]["start_s"] + actual["peak_s"] - 3) < 0.0001,
            "incorrect visual placement",
        )
        require(actual["sha256"] == r["audio"]["sha256"], "hash mismatch")
        return {"independent_pcm": actual, "placement": r["placement"]}

    def repeatable_seed(self):
        a, b = self.render("a.wav"), self.render("b.wav")
        require(
            pcm(a["audio"]["file"])["sha256"] == pcm(b["audio"]["file"])["sha256"],
            "seed not repeatable",
        )
        return {"sha256": a["audio"]["sha256"]}

    def resampled_pitch(self):
        r = self.call(
            "render",
            "pluck/kalimba",
            "--pitch",
            "E5",
            "--dur",
            "0.65",
            "--sr",
            "44100",
            "--out",
            self.case_dir / "e5.wav",
        )
        actual = pcm(r["audio"]["file"])
        require(
            actual["frames"] == 28665 and actual["sr"] == 44100,
            "bad output resampling/duration",
        )
        require("pitch" in r["render_meta"]["edits"], "pitch result missing")
        return {"pcm": actual, "pitch": r["render_meta"]["edits"]["pitch"]}

    def fitted_bank_entry(self):
        entries = [r for r in self.call("list")["sounds"] if r["type"] == "fit"]
        r = self.call("render", entries[0]["id"], "--out", self.case_dir / "fit.wav")
        require(
            not r["runtime"]["forbidden_packages"],
            "fit entry brought heavy dependencies",
        )
        return {"sound": entries[0]["id"], "pcm": pcm(r["audio"]["file"])}

    def kit_and_cache(self):
        spec = SKILL / "assets" / "kits" / "video-ui.json"
        a = self.call("kit", "render", spec, "--out", self.case_dir / "takes")
        require(len(a["assets"]) == 10, "expected 10 configured takes")
        for asset in a["assets"]:
            require(
                pcm(asset["file"])["sha256"] == asset["sha256"],
                "kit take hash mismatch",
            )
        b = self.call("kit", "render", spec, "--out", self.case_dir / "takes")
        require(
            b["kit"]["stats"]["cached"] == 10 and b["kit"]["stats"]["rendered"] == 0,
            "kit cache failed",
        )
        return {"first": a["kit"]["stats"], "second": b["kit"]["stats"]}

    def custom_wooden_tap(self):
        recipe = SKILL / "assets" / "recipes" / "wooden_tap.py"
        r = self.call(
            "custom",
            "--recipe",
            recipe,
            "--params",
            '{"duration":0.24,"body_hz":180}',
            "--seed",
            "17",
            "--out",
            self.case_dir / "tap.wav",
        )
        require(
            r["source"]["recipe_sha256"]
            == hashlib.sha256(recipe.read_bytes()).hexdigest(),
            "wrong recipe hash",
        )
        actual = pcm(r["audio"]["file"])
        require(actual["frames"] == 11520, "custom duration ignored")
        return {"pcm": actual, "source": r["source"]}

    def unsupported_pitch(self):
        target = self.case_dir / "bad.wav"
        r = self.call(
            "render", "whoosh_fast/crisp", "--pitch", "C5", "--out", target, fail=True
        )
        require(not target.exists(), "unsupported request wrote output")
        return r

    def preserve_existing_output(self):
        target = self.case_dir / "keep.wav"
        target.write_bytes(b"existing project asset")
        self.call("render", "click/soft", "--out", target, fail=True)
        require(
            target.read_bytes() == b"existing project asset",
            "existing asset overwritten",
        )
        return {"preserved": True}

    def negative_placement(self):
        r = self.render("early.wav", "--align", "peak", "--cue-at", "0.1")
        p = r["placement"]
        require(p["start_s"] < 0 and p["pre_roll_s"] > 0, "negative start clamped")
        require(
            abs(p["start_s"] + p["anchor_s"] - 0.1) < 0.0001, "bad pre-roll placement"
        )
        return p

    def invalid_custom_audio(self):
        recipe = self.case_dir / "invalid.py"
        recipe.write_text(
            "import numpy as np\ndef render(params, rng):\n    return np.array([np.nan, 0.0])\n"
        )
        target = self.case_dir / "bad.wav"
        r = self.call("custom", "--recipe", recipe, "--out", target, fail=True)
        require(
            not target.exists() and not target.with_suffix(".meta.json").exists(),
            "invalid signal wrote output",
        )
        return r

    def resampling_peak_target(self):
        a = self.call(
            "render",
            "pro_click/glass",
            "--sr",
            "96000",
            "--peak-db",
            "0",
            "--out",
            self.case_dir / "bank.wav",
        )
        b = self.call(
            "custom",
            "--recipe",
            SKILL / "assets/recipes/wooden_tap.py",
            "--sr",
            "96000",
            "--peak-db",
            "0",
            "--out",
            self.case_dir / "custom.wav",
        )
        for r in (a, b):
            require(
                abs(r["audio"]["peak_db"]) < 0.01,
                "resampling changed requested sample-peak level",
            )
            require(r["audio"]["sr"] == 96000, "output sample rate ignored")
        return {
            "bank_peak_db": a["audio"]["peak_db"],
            "custom_peak_db": b["audio"]["peak_db"],
        }

    def invalid_kit_check(self):
        a = self.call("kit", "check", self.case_dir / "missing.json", fail=True)
        invalid = self.case_dir / "unknown.json"
        invalid.write_text(
            json.dumps({"kit": 1, "roles": {"click": {"sound": "unknown/sound"}}})
        )
        b = self.call("kit", "check", invalid, fail=True)
        return {"missing": a, "unknown_sound": b}

    def resampled_kit(self):
        spec = self.case_dir / "kit.json"
        spec.write_text(
            json.dumps(
                {
                    "kit": 1,
                    "sr": 96000,
                    "roles": {
                        "click": {
                            "sound": "pro_click/glass",
                            "seed": 42,
                            "edits": {"peak_db": 0},
                        },
                        "click.light": {
                            "sound": "pro_click/glass",
                            "seed": 42,
                            "edits": {"peak_db": 0, "weight": 0.5},
                        },
                    },
                }
            )
        )
        out = self.case_dir / "takes"
        result = self.call("kit", "render", spec, "--out", out)
        lock_path = out / "kit.lock.json"
        lock = json.loads(lock_path.read_text())
        for asset in result["assets"]:
            weight = 0.5 if asset["role"] == "click.light" else 1
            single = self.call(
                "render",
                "pro_click/glass",
                "--sr",
                "96000",
                "--peak-db",
                "0",
                "--weight",
                weight,
                "--seed",
                asset["seed"],
                "--out",
                self.case_dir / f"single-{weight}.wav",
            )
            require(
                pcm(asset["file"])["sha256"] == single["audio"]["sha256"],
                "kit resampling differs from the normalized single take",
            )
            take = lock["roles"][asset["role"]]["takes"][0]
            require(
                all(
                    take[k] == asset[k]
                    for k in ("onset_s", "peak_s", "end_s", "dur_s", "peak_db")
                ),
                "kit lock does not describe final PCM",
            )
        cached = self.call("kit", "render", spec, "--out", out)
        require(
            cached["kit"]["stats"]["cached"] == 2, "normalized takes are not cached"
        )
        lock.pop("skill_renderer_revision", None)
        lock_path.write_text(json.dumps(lock))
        migrated = self.call("kit", "render", spec, "--out", out)
        require(
            migrated["kit"]["stats"]["rendered"] == 2,
            "legacy resampled cache was reused",
        )
        return {
            "assets": result["assets"],
            "cache_stats": cached["kit"]["stats"],
            "migration_stats": migrated["kit"]["stats"],
        }

    def custom_recipe_diagnostics(self):
        recipe = self.case_dir / "verbose.py"
        recipe.write_text(
            'import numpy as np\nprint("loading recipe")\n'
            'def render(params, rng):\n    print("rendering recipe")\n'
            "    return np.sin(np.arange(2400) * (2 * np.pi * 440 / 48000))\n"
        )
        result = self.call(
            "custom", "--recipe", recipe, "--out", self.case_dir / "verbose.wav"
        )
        actual = pcm(result["audio"]["file"])
        require(actual["frames"] == 2400, "verbose recipe did not render")
        log = (self.case_dir / "command-1.log").read_text()
        require(
            "loading recipe" in log and "rendering recipe" in log,
            "recipe diagnostics were lost",
        )
        return actual

    def full_bank(self):
        entries = self.call("list")["sounds"]
        warnings = []

        def render_entry(pair):
            i, entry = pair
            directory = self.case_dir / f"{i:03}-{entry['id'].replace('/', '-')}"
            directory.mkdir(parents=True, exist_ok=True)
            child = Runner(directory, self.offline)
            r = child.call("render", entry["id"], "--out", directory / "sound.wav")
            actual = pcm(r["audio"]["file"])
            require(
                actual["sha256"] == r["audio"]["sha256"], "incorrect bank artifact hash"
            )
            require(
                not r["runtime"]["forbidden_packages"],
                "heavy dependency in bank render",
            )
            return {"sound": entry["id"], "warnings": r["audio"]["checks"]["warnings"]}

        with ThreadPoolExecutor(max_workers=self.jobs) as pool:
            for i, result in enumerate(pool.map(render_entry, enumerate(entries)), 1):
                if result["warnings"]:
                    warnings.append(result)
                if i % 25 == 0:
                    print(
                        f"full-bank: {i}/{len(entries)} rendered",
                        file=sys.stderr,
                        flush=True,
                    )
        return {
            "rendered": len(entries),
            "technical_warnings": warnings,
            "note": "Successful rendering does not imply every sound is technically warning-free or good by taste.",
        }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--suite", choices=("smoke", "bank"), default="smoke")
    p.add_argument("--offline", action="store_true")
    p.add_argument(
        "--jobs",
        type=int,
        choices=range(1, 9),
        default=2,
        help="Concurrent full-bank renders (1–8)",
    )
    args = p.parse_args()
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    require(not (out / "report.json").exists(), "Choose a fresh eval output directory")
    cases = json.loads((SKILL / "evals" / "evals.json").read_text())["evals"]
    selected = [c for c in cases if c.get("automated")]
    if args.suite == "bank":
        selected.append({"id": "bank", "name": "full-bank"})
    runner, results = Runner(out, args.offline, args.jobs), []
    for case in selected:
        start = time.monotonic()
        try:
            evidence = runner.case(case["name"])
            result = {
                "id": case["id"],
                "name": case["name"],
                "passed": True,
                "evidence": evidence,
            }
        except Exception as e:  # noqa: BLE001 - record each failing artifact case and continue the suite.
            result = {
                "id": case["id"],
                "name": case["name"],
                "passed": False,
                "error": f"{type(e).__name__}: {e}",
            }
        result["seconds"] = round(time.monotonic() - start, 3)
        results.append(result)
        print(
            f"{case['name']}: {'PASS' if result['passed'] else 'FAIL'}",
            file=sys.stderr,
            flush=True,
        )
    report = {
        "suite": args.suite,
        "passed": sum(r["passed"] for r in results),
        "total": len(results),
        "agent_evals_run": False,
        "human_listening_run": False,
        "results": results,
    }
    (out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "report": str(out / "report.json"),
                "passed": report["passed"],
                "total": report["total"],
            }
        )
    )
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
