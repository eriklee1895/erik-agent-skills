#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Generate, edit, and batch-create images through the OpenRouter unified image API.

Supported model shortlist (deliberately curated, not the full OpenRouter catalog):
  sunburst  openai/gpt-image-2.5-sunburst   precision tier (quality 6 tiers, n<=10)
  flare     openai/gpt-image-2.5-flare      speed tier  (same parameter matrix)
  banana    google/gemini-3.1-flash-image   Nano Banana 2 (resolution tiers, n=1)

The two GPT models and the Gemini model speak different parameter dialects;
this script validates requests against each model's matrix before calling.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://openrouter.ai/api/v1/images"

# Parameter matrices transcribed from
# GET https://openrouter.ai/api/v1/images/models (2026-09-30).
MODELS: dict[str, dict] = {
    "sunburst": {
        "id": "openai/gpt-image-2.5-sunburst",
        "dialect": "gpt",
        "aspect_ratios": ["1:1", "3:2", "2:3", "4:3", "3:4",
                          "16:9", "9:16", "21:9", "auto"],
        "qualities": ["auto", "low", "medium", "high", "xhigh", "max"],
        "backgrounds": ["auto", "transparent", "opaque"],
        "n_max": 10,
        "refs_max": 16,
        "streaming": True,
    },
    "flare": {
        "id": "openai/gpt-image-2.5-flare",
        "dialect": "gpt",
        "aspect_ratios": ["1:1", "3:2", "2:3", "4:3", "3:4",
                          "16:9", "9:16", "21:9", "auto"],
        "qualities": ["auto", "low", "medium", "high", "xhigh", "max"],
        "backgrounds": ["auto", "transparent", "opaque"],
        "n_max": 10,
        "refs_max": 16,
        "streaming": True,
    },
    "banana": {
        "id": "google/gemini-3.1-flash-image",
        "dialect": "banana",
        "aspect_ratios": ["1:1", "1:4", "1:8", "2:3", "3:2", "3:4",
                          "4:1", "4:3", "4:5", "5:4", "8:1", "9:16",
                          "16:9", "21:9"],
        "resolutions": ["512", "1K", "2K", "4K"],
        "n_max": 1,
        "refs_max": 14,
        "streaming": False,
    },
}

ALIASES = {m["id"]: name for name, m in MODELS.items()}


def resolve_model(value: str) -> str:
    if not isinstance(value, str):
        raise SystemExit("model must be a string (alias or full OpenRouter id).")
    if value in MODELS:
        return value
    if value in ALIASES:
        return ALIASES[value]
    known = ", ".join([*MODELS, *ALIASES])
    raise SystemExit(f"unknown model '{value}'. This skill supports: {known}.")


def load_env():
    """Pick up OPENROUTER_API_KEY from a .env in cwd or parents."""
    cur = Path.cwd()
    for d in [cur, *cur.parents]:
        p = d / ".env"
        if p.is_file():
            for raw in p.read_text().splitlines():
                line = raw.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break


def data_url(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(suffix)
    if not mime:
        raise SystemExit(f"reference must be png/jpg/webp: {path}")
    if not path.is_file():
        raise SystemExit(f"reference not found: {path}")
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def build_request(model_name: str, prompt: str, aspect: str, quality: str | None,
                  resolution: str | None, background: str | None, n: int,
                  refs: list[Path], compression: int | None) -> dict:
    m = MODELS[model_name]

    # ---- validation (errors before any network call) ----
    if aspect not in m["aspect_ratios"]:
        raise SystemExit(
            f"{model_name} does not accept aspect_ratio '{aspect}'. Allowed: "
            f"{', '.join(m['aspect_ratios'])}")
    if type(n) is not int:
        raise SystemExit("n must be an integer.")
    if n < 1 or n > m["n_max"]:
        raise SystemExit(
            f"{model_name} returns at most n={m['n_max']} image(s) per request; got n={n}.")
    if len(refs) > m["refs_max"]:
        raise SystemExit(
            f"{model_name} accepts at most {m['refs_max']} reference image(s); "
            f"got {len(refs)}.")
    if not isinstance(prompt, str) or not prompt.strip():
        raise SystemExit("prompt must be a non-empty string.")
    if compression is not None and type(compression) is not int:
        raise SystemExit("output_compression must be an integer.")

    body: dict = {"model": m["id"], "prompt": prompt, "aspect_ratio": aspect, "n": n}

    if refs:
        body["input_references"] = [
            {"type": "image_url", "image_url": {"url": data_url(p)}} for p in refs
        ]

    if m["dialect"] == "gpt":
        if resolution is not None:
            raise SystemExit(
                f"{model_name} has no 'resolution' parameter — it uses '--quality' "
                "(low..max) and aspect_ratio instead. Drop --resolution.")
        if quality is not None and quality not in m["qualities"]:
            raise SystemExit(
                f"{model_name} does not accept quality '{quality}'. Allowed: "
                f"{', '.join(m['qualities'])}")
        body["quality"] = "auto" if quality is None else quality
        if background is not None:
            if background not in m["backgrounds"]:
                raise SystemExit(f"unknown background '{background}'.")
            if background != "auto":
                body["background"] = background
        if compression is not None:
            body["output_compression"] = compression
    else:  # banana
        if quality is not None:
            raise SystemExit(
                f"{model_name} (Nano Banana 2) has no 'quality' tiers — it uses "
                "'--resolution' (512/1K/2K/4K). Drop --quality.")
        if background is not None:
            raise SystemExit(
                f"{model_name} has no background control and cannot produce "
                "transparent PNGs. Use sunburst/flare for that.")
        if compression is not None:
            raise SystemExit(f"{model_name} does not support output_compression.")
        if resolution is not None and resolution not in m["resolutions"]:
            raise SystemExit(
                f"{model_name} does not accept resolution '{resolution}'. Allowed: "
                f"{', '.join(m['resolutions'])}")
        body["resolution"] = "1K" if resolution is None else resolution

    return body


def call_api(body: dict, timeout: int) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit(
            "OPENROUTER_API_KEY is not set. Add it to your environment or a .env file: "
            "OPENROUTER_API_KEY=sk-or-...  (create at https://openrouter.ai/keys)")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/eriklee1895/erik-agent-skills",
        "X-Title": "openrouter-image skill",
    }
    req = urllib.request.Request(
        API_URL, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def save_images(resp: dict, out: Path) -> list[Path]:
    items = resp.get("data") or []
    if not items:
        raise SystemExit(f"response contained no images: {json.dumps(resp)[:300]}")
    out.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, item in enumerate(items):
        b64 = item.get("b64_json")
        if not b64:
            raise SystemExit(f"data[{i}] has no b64_json: {json.dumps(item)[:200]}")
        target = out if len(items) == 1 else out.with_name(
            f"{out.stem}-{i + 1}{out.suffix}")
        target.write_bytes(base64.b64decode(b64))
        paths.append(target)
    return paths


def write_meta(out: Path, body: dict, resp: dict, elapsed: float, paths: list[Path]):
    meta = {
        "provider": "openrouter",
        "request_model": body["model"],
        "request": body,
        "outputs": [str(p) for p in paths],
        "usage": resp.get("usage"),
        "elapsed_seconds": round(elapsed, 1),
    }
    out.with_suffix(".json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1))


# ----------------------------- batch -----------------------------

BATCH_FIELDS = {
    "name", "model", "prompt", "aspect_ratio", "aspect", "quality", "resolution",
    "n", "background", "images", "output_compression",
}


def prepare_batch_job(job: dict, line_number: int, out_dir: Path) -> dict:
    """Normalize and validate one JSONL job without network or output writes."""
    if not isinstance(job, dict):
        raise SystemExit("each job must be a JSON object.")
    unknown = set(job) - BATCH_FIELDS
    if unknown:
        raise SystemExit(f"unknown job field(s): {', '.join(sorted(unknown))}.")
    for field, value in job.items():
        if value is None:
            raise SystemExit(f"{field} cannot be null; omit it to use the default.")
    if "prompt" not in job:
        raise SystemExit("prompt is required.")
    if "aspect_ratio" in job and "aspect" in job and job["aspect_ratio"] != job["aspect"]:
        raise SystemExit("conflicting aspect_ratio and legacy aspect values; use aspect_ratio.")

    model_name = resolve_model(job.get("model", "sunburst"))
    # Keep existing unnamed output names based on the physical, zero-based row.
    name = job.get("name", f"job-{line_number - 1:03d}")
    if not isinstance(name, str) or not name.strip():
        raise SystemExit("name must be a non-empty string.")
    images = job.get("images", [])
    if not isinstance(images, list) or any(
            not isinstance(path, str) or not path.strip() for path in images):
        raise SystemExit("images must be a list of non-empty reference path strings.")
    body = build_request(
        model_name,
        job["prompt"],
        job.get("aspect_ratio", job.get("aspect", "1:1")),
        job.get("quality"),
        job.get("resolution"),
        job.get("background"),
        job.get("n", 1),
        [Path(path) for path in images],
        job.get("output_compression"),
    )
    return {"line": line_number, "name": name, "model_alias": model_name,
            "request": body, "outputs": [str(out_dir / f"{name}.png")]}


def preflight_batch(input_path: Path, out_dir: Path) -> list[dict]:
    """Prepare every request before allowing any paid execution."""
    jobs = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if line and not line.startswith("#"):
            try:
                job = json.loads(line)
                jobs.append(prepare_batch_job(job, line_number, out_dir))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"batch line {line_number}: invalid JSON: {exc.msg}.") from None
            except (SystemExit, OSError) as exc:
                raise SystemExit(f"batch line {line_number}: {exc}") from None
    return jobs


def run_batch(input_path: Path, out_dir: Path, timeout: int, dry_run: bool = False):
    jobs = preflight_batch(input_path, out_dir)
    if dry_run:
        print(json.dumps({"jobs": jobs}, ensure_ascii=False, indent=1))
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"batch: {len(jobs)} job(s)")

    summary = []
    for job in jobs:
        name, body = job["name"], job["request"]
        out = Path(job["outputs"][0])
        t = time.time()
        try:
            resp = call_api(body, timeout)
            paths = save_images(resp, out)
            write_meta(out, body, resp, time.time() - t, paths)
            status, cost = "ok", (resp.get("usage") or {}).get("cost")
            print(f"  [line {job['line']}] ok  {name} -> {', '.join(str(p) for p in paths)} (${cost})")
        except urllib.error.HTTPError as e:
            status = f"HTTP {e.code}: {e.read().decode()[:200]}"
            print(f"  [line {job['line']}] FAIL {name}: {status}")
        summary.append({"name": name, "status": status})

    (out_dir / "batch-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1))


# ----------------------------- main -----------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p):
        p.add_argument("--model", default="sunburst",
                       help="sunburst | flare | banana (or full OpenRouter id)")
        p.add_argument("--prompt")
        p.add_argument("--prompt-file")
        p.add_argument("--aspect", default="1:1", help="aspect_ratio, e.g. 16:9")
        p.add_argument("--n", type=int, default=1)
        p.add_argument("--image", action="append", default=[],
                       help="reference image (repeatable)")
        p.add_argument("--out", required=True)
        p.add_argument("--timeout", type=int, default=600)
        p.add_argument("--dry-run", action="store_true")

    g = sub.add_parser("generate", help="text-to-image")
    add_common(g)
    g.add_argument("--quality", help="auto|low|medium|high|xhigh|max (GPT models)")
    g.add_argument("--resolution", help="512|1K|2K|4K (banana)")
    g.add_argument("--background", help="transparent|opaque (GPT models)")
    g.add_argument("--output-compression", type=int)

    e = sub.add_parser("edit", help="reference-guided edit / composite")
    add_common(e)
    e.add_argument("--quality")
    e.add_argument("--resolution")
    e.add_argument("--background")
    e.add_argument("--output-compression", type=int)

    b = sub.add_parser("batch", help="run jobs from a JSONL file")
    b.add_argument("--input", required=True)
    b.add_argument("--out-dir", required=True)
    b.add_argument("--timeout", type=int, default=600)
    b.add_argument("--dry-run", action="store_true",
                   help="validate all jobs and print requests without calling the API or writing outputs")

    args = parser.parse_args()
    load_env()

    if args.command == "batch":
        run_batch(Path(args.input), Path(args.out_dir), args.timeout, args.dry_run)
        return

    model_name = resolve_model(args.model)
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text()
    elif args.prompt:
        prompt = args.prompt
    else:
        raise SystemExit("provide --prompt or --prompt-file.")

    refs = [Path(p) for p in args.image]
    body = build_request(
        model_name, prompt, args.aspect, args.quality, args.resolution,
        args.background, args.n, refs, args.output_compression)
    out = Path(args.out)

    if args.dry_run:
        print(json.dumps({"model_alias": model_name, "request": body,
                          "outputs": [str(out)]}, ensure_ascii=False, indent=1))
        return

    t = time.time()
    try:
        resp = call_api(body, args.timeout)
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        raise SystemExit(f"OpenRouter rejected the request (HTTP {e.code}):\n{detail}")
    elapsed = time.time() - t
    paths = save_images(resp, out)
    write_meta(out, body, resp, elapsed, paths)
    cost = (resp.get("usage") or {}).get("cost")
    print(f"saved {len(paths)} image(s) in {elapsed:.0f}s (${cost}):")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
