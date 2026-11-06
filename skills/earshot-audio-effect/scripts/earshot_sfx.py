#!/usr/bin/env -S uv run --locked --script
# /// script
# requires-python = ">=3.11,<3.15"
# dependencies = [
#   "earshot @ git+https://github.com/Leonxlnx/earshot.git@925ebe56a1b755e5d354ab642bb8f344440cfa9c",
# ]
# [[tool.uv.dependency-metadata]]
# name = "earshot"
# version = "0.3.0"
# requires-python = ">=3.10"
# requires-dist = ["numpy>=1.26", "scipy>=1.11", "soundfile>=0.12", "soxr>=0.3"]
# ///
"""CPU sound effects: dynamic bank, single takes, kits, and project DSP recipes.

Run with uv; the inline uv metadata intentionally selects Earshot's generation
dependencies instead of its upstream all-features dependency declaration.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

UPSTREAM_COMMIT = "925ebe56a1b755e5d354ab642bb8f344440cfa9c"
UPSTREAM_VERSION = "0.3.0"
KIT_RENDERER_REVISION = 1
FORBIDDEN = ("torch", "transformers")
SAMPLE_RATES = (44100, 48000, 88200, 96000)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def number(value):
    n = float(value)
    if not math.isfinite(n):
        raise argparse.ArgumentTypeError("number must be finite")
    return n


def positive(value):
    n = number(value)
    if n <= 0:
        raise argparse.ArgumentTypeError("number must be greater than zero")
    return n


def nonnegative(value):
    n = number(value)
    if n < 0:
        raise argparse.ArgumentTypeError("number must be nonnegative")
    return n


def runtime_info():
    import earshot
    from earshot.forge import bank

    packages = {
        d.metadata["Name"].lower(): d.version
        for d in importlib.metadata.distributions()
    }
    return {
        "python": sys.version.split()[0],
        "earshot": earshot.__version__,
        "upstream_commit": UPSTREAM_COMMIT,
        "bank": bank.VERSION,
        "packages": dict(sorted(packages.items())),
        "forbidden_packages": [p for p in FORBIDDEN if p in packages],
        "forbidden_modules_loaded": sorted(
            {n.split(".")[0] for n in sys.modules if n.split(".")[0] in FORBIDDEN}
        ),
    }


def assert_runtime():
    info = runtime_info()
    if info["earshot"] != UPSTREAM_VERSION:
        raise RuntimeError(
            "Use uv run --script with the bundled lockfile; unexpected Earshot version"
        )
    if info["forbidden_packages"] or info["forbidden_modules_loaded"]:
        raise RuntimeError(
            "This generation environment must not contain or load torch/transformers; use uv run --script"
        )
    return info


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    def scalar(v):
        if hasattr(v, "item"):
            return v.item()
        raise TypeError(f"Cannot serialize {type(v).__name__}")

    return (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=scalar)
        + "\n"
    )


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(encode(value))
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def targets(out, force=False):
    path = Path(out).expanduser().resolve()
    if path.suffix.lower() != ".wav":
        raise ValueError("Output must use the .wav extension (PCM 24-bit)")
    meta = path.with_suffix(".meta.json")
    if not force:
        for p in (path, meta):
            if p.exists():
                raise FileExistsError(
                    f"{p} exists; choose a new output or pass --force"
                )
    return path, meta


def valid_signal(y):
    import numpy as np

    x = np.asarray(y, dtype=np.float64)
    if x.ndim not in (1, 2) or (x.ndim == 2 and x.shape[1] not in (1, 2)):
        raise ValueError(
            "Recipe must return mono (frames,) or mono/stereo (frames, 1|2)"
        )
    if len(x) < 2 or not np.isfinite(x).all() or np.abs(x).max() < 1e-7:
        raise ValueError("Audio is empty, non-finite, or silent")
    return x


def inspect_audio(path, category=None, role=None, sound=None):
    import soundfile as sf
    from earshot.forge import bank, sfx

    y, sr = sf.read(str(path), dtype="float64")
    valid_signal(y)
    measured = bank.measure(y, sr=sr)
    info = sf.info(str(path))
    return {
        "file": str(Path(path).resolve()),
        "sha256": sha256(path),
        "sr": sr,
        "frames": info.frames,
        "channels": info.channels,
        "subtype": info.subtype,
        **measured,
        "duration_s": info.frames / sr,
        "checks": sfx.check(
            y, sr=sr, category=category, role=role, sound=sound or Path(path).name
        ),
    }


def placement(audio, align, cue_at):
    anchor = audio[align + "_s"]
    result = {"align": align, "anchor_s": anchor}
    if cue_at is not None:
        result.update(cue_at_s=cue_at, start_s=round(cue_at - anchor, 6))
        if result["start_s"] < 0:
            result["pre_roll_s"] = round(-result["start_s"], 6)
    return result


def save_take(
    y, sr, out, source, align="onset", cue_at=None, force=False, render_meta=None
):
    import soundfile as sf

    path, meta_path = targets(out, force)
    x = valid_signal(y)
    if abs(x).max() > 1.000001:
        raise ValueError(
            "Audio exceeds full scale; normalize the recipe before writing PCM"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(suffix=".wav", prefix="." + path.stem, dir=path.parent)
    os.close(fd)
    try:
        sf.write(temp, x, sr, subtype="PCM_24")
        audio = inspect_audio(
            temp, category=source.get("category"), sound=source.get("sound", path.name)
        )
        audio["file"] = str(path)
        report = {
            "ok": True,
            "schema": 1,
            "source": source,
            "audio": audio,
            "placement": placement(audio, align, cue_at),
            "runtime": assert_runtime(),
            "metadata_file": str(meta_path),
        }
        if render_meta is not None:
            report["render_meta"] = render_meta
        encode(report)  # Validate the complete metadata before replacing either output.
        os.replace(temp, path)
        write_json(meta_path, report)
        return report
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def render(args):
    from earshot.forge import bank

    targets(args.out, args.force)
    if args.dur is not None and args.apex is not None and args.apex >= args.dur:
        raise ValueError("--apex must be earlier than --dur")
    knobs = {
        k: getattr(args, k)
        for k in ("seed", "dur", "apex", "pitch", "peak_db", "sr", "weight")
    }
    y, meta = bank.render(args.sound, **knobs)
    if args.sr != 48000:
        y = bank.normalize(y, bank.level(args.peak_db, args.weight))
    return save_take(
        y,
        args.sr,
        args.out,
        {
            "kind": "bank",
            "sound": args.sound,
            "category": bank.get(args.sound)["category"],
            "seed": meta["seed"],
            "requested": knobs,
        },
        args.align,
        args.cue_at,
        args.force,
        meta,
    )


def custom(args):
    import numpy as np
    import soxr
    from earshot.forge import dsp

    targets(args.out, args.force)
    recipe_path = Path(args.recipe).expanduser().resolve(strict=True)
    params = json.loads(args.params)
    if not isinstance(params, dict):
        raise TypeError("--params must be a JSON object")
    encode(params)
    spec = importlib.util.spec_from_file_location("earshot_project_recipe", recipe_path)
    if spec is None or spec.loader is None:
        raise ValueError("Recipe must be a Python .py file")
    recipe = importlib.util.module_from_spec(spec)
    with redirect_stdout(sys.stderr):
        spec.loader.exec_module(recipe)
        if not callable(getattr(recipe, "render", None)):
            raise TypeError(
                "Recipe must define render(params, rng), returning a 48 kHz numpy array"
            )
        defaults = dict(getattr(recipe, "DEFAULTS", {}))
        defaults.update(params)
        y = valid_signal(recipe.render(defaults, dsp.rng(args.seed)))
    y = dsp.normalize(dsp.fade(y, fin=args.fade_in, fout=args.fade_out), args.peak_db)
    if args.sr != dsp.SR:
        y = np.asarray(soxr.resample(y, dsp.SR, args.sr), np.float64)
        y = dsp.normalize(y, args.peak_db)
    return save_take(
        y,
        args.sr,
        args.out,
        {
            "kind": "custom",
            "recipe_file": str(recipe_path),
            "recipe_sha256": sha256(recipe_path),
            "params": defaults,
            "seed": args.seed,
            "post": {
                "fade_in_s": args.fade_in,
                "fade_out_s": args.fade_out,
                "peak_db": args.peak_db,
            },
        },
        args.align,
        args.cue_at,
        args.force,
    )


def render_kit(spec, out, force):
    """Keep the pinned kit planner/cache, repairing its nonnative-rate PCM writer."""
    import soundfile as sf
    from earshot.forge import bank, kit, sfx

    config = kit.load(spec)
    if config.get("sr", 48000) == 48000:
        return kit.render(config, str(out), force=force)
    previous = out / "kit.lock.json"
    if previous.exists():
        try:
            revision = json.loads(previous.read_text()).get("skill_renderer_revision")
        except (OSError, ValueError, AttributeError):
            revision = None
        force = force or revision != KIT_RENDERER_REVISION
    planned = {take["file"]: take for take in kit.plan(config)}
    original_write = sfx.write

    def write_resampled_take(path, y, sr=48000):
        edits = planned[Path(path).name]["edits"]
        x = valid_signal(
            bank.normalize(
                y, bank.level(edits.get("peak_db", -1.0), edits.get("weight"))
            )
        )
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), x, sr, subtype="PCM_24")
        return str(path).replace(chr(92), "/")

    # The immutable upstream kit writes only its final takes through sfx.write.
    # Scope the adapter to this CLI operation; never edit the installed source.
    sfx.write = write_resampled_take
    try:
        return kit.render(config, str(out), force=force)
    finally:
        sfx.write = original_write


def run_kit(args):
    from earshot.forge import bank, kit

    if args.kit_command == "init":
        result = kit.init(
            args.preset, str(Path(args.out).expanduser().resolve()), args.force
        )
        return {"ok": True, **result}
    spec = str(Path(args.kit).expanduser().resolve())
    if args.kit_command == "check":
        kit.load(spec)  # Invalid configuration is an error, not a successful audit.
        checks = kit.check(spec)  # Memory renders keep this path independent of FFmpeg.
        errors = [
            w["msg"]
            for rows in checks["roles"].values()
            for row in rows
            for w in row["warnings"]
            if w["code"] == "render"
        ]
        if errors:
            raise kit.KitError("; ".join(errors))
        return {"ok": True, "checks": checks}
    out = Path(args.out).expanduser().resolve()
    result = render_kit(spec, out, args.force)
    assets = []
    for role, record in result["roles"].items():
        if record:
            for take in record["takes"]:
                audio = inspect_audio(
                    out / take["file"],
                    category=bank.get(record["sound"])["category"],
                    role=role,
                    sound=record["sound"],
                )
                if "pitch_off" in take["checks"]:
                    bank.add_warning(
                        audio["checks"],
                        {
                            "code": "pitch_off",
                            "msg": f"Pitch {take['pitch']}: the upstream knob did not land the note",
                        },
                    )
                for key in (
                    "onset_s",
                    "peak_s",
                    "end_s",
                    "dur_s",
                    "peak_db",
                    "lufs_m_max",
                ):
                    take[key] = audio[key]
                take["checks"] = [w["code"] for w in audio["checks"]["warnings"]]
                assets.append(
                    {
                        **audio,
                        "role": role,
                        "sound": record["sound"],
                        "seed": take["seed"],
                        "align": record["align"],
                        "level_db": record["level_db"],
                    }
                )
    result["skill_renderer_revision"] = KIT_RENDERER_REVISION
    lock = {k: v for k, v in result.items() if k not in ("stats", "summary", "file")}
    write_json(out / "kit.lock.json", lock)
    warnings = sorted(
        {
            f"{asset['role']}:{warning['code']}"
            for asset in assets
            for warning in asset["checks"]["warnings"]
        }
    )
    stats = result["stats"]
    result["summary"] = (
        f"kit {result.get('name') or ''}: {len(assets)} takes "
        f"({stats['rendered']} rendered, {stats['cached']} cached); "
        + ("warnings: " + ", ".join(warnings) if warnings else "checks clean")
    )
    report = {
        "ok": True,
        "schema": 1,
        "kit": result,
        "assets": assets,
        "runtime": assert_runtime(),
        "metadata_file": str(out / "manifest.json"),
    }
    write_json(out / "manifest.json", report)
    return report


def parser():
    p = Parser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "doctor", help="Report the pinned runtime and installed/loaded dependencies"
    )
    ls = sub.add_parser(
        "list", help="Query the actual upstream bank, not a copied catalog"
    )
    ls.add_argument("--category")
    ls.add_argument("--kind")
    r = sub.add_parser("render", help="Render one bank sound")
    r.add_argument("sound")
    r.add_argument("--seed", type=int)
    r.add_argument("--dur", type=positive)
    r.add_argument("--apex", type=nonnegative)
    r.add_argument("--pitch")
    r.add_argument("--weight", type=positive)
    c = sub.add_parser(
        "custom", help="Execute a project-owned render(params, rng) recipe"
    )
    c.add_argument("--recipe", required=True)
    c.add_argument(
        "--params", default="{}", help="JSON object merged over the recipe DEFAULTS"
    )
    c.add_argument("--seed", type=int, default=0)
    c.add_argument("--fade-in", type=nonnegative, default=0.001)
    c.add_argument("--fade-out", type=nonnegative, default=0.02)
    for cmd in (r, c):
        cmd.add_argument("--out", required=True)
        cmd.add_argument("--peak-db", type=number, default=-3.0)
        cmd.add_argument("--sr", type=int, choices=SAMPLE_RATES, default=48000)
        cmd.add_argument("--align", choices=("onset", "peak", "end"), default="onset")
        cmd.add_argument("--cue-at", type=nonnegative)
        cmd.add_argument("--force", action="store_true")
    check = sub.add_parser(
        "check", help="Measure a delivered WAV; no semantic or taste scoring"
    )
    check.add_argument("file")
    k = sub.add_parser("kit", help="Prepare or render an upstream role-based sound kit")
    ks = k.add_subparsers(dest="kit_command", required=True)
    ki = ks.add_parser("init")
    ki.add_argument("--preset", choices=("calm", "crisp", "minimal"), default="calm")
    ki.add_argument("--out", required=True)
    ki.add_argument("--force", action="store_true")
    for name in ("render", "check"):
        kr = ks.add_parser(name)
        kr.add_argument("kit")
        if name == "render":
            kr.add_argument("--out", required=True)
            kr.add_argument("--force", action="store_true")
    return p


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        if getattr(args, "peak_db", 0) > 0:
            raise ValueError("--peak-db must not exceed 0 dBFS")
        runtime = assert_runtime()
        if args.command == "doctor":
            from earshot.forge import bank, kit

            result = {
                "ok": True,
                "runtime": runtime,
                "sounds": len(bank.ids()),
                "kit_presets": kit.presets(),
            }
        elif args.command == "list":
            from earshot.forge import sfx

            result = {
                "ok": True,
                **sfx.sfx_list(category=args.category, kind=args.kind),
            }
        elif args.command == "render":
            result = render(args)
        elif args.command == "custom":
            result = custom(args)
        elif args.command == "kit":
            result = run_kit(args)
        else:
            result = {
                "ok": True,
                "audio": inspect_audio(Path(args.file).expanduser().resolve()),
            }
        assert_runtime()
        print(encode(result), end="")
        return 0
    except Exception as e:  # noqa: BLE001 - upstream and recipe failures share the CLI error protocol.
        print(
            encode({"ok": False, "error": str(e), "error_type": type(e).__name__}),
            end="",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
