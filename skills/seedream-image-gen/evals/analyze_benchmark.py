#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=10.1.0"]
# ///
"""Analyze local study outputs; optionally export explicit, URL-free fields."""

import argparse
from collections import Counter
import hashlib
import json
import random
import statistics
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat


def load(root):
    manifest = json.loads((root / "cases.json").read_text())
    records = {
        p.parent.name: json.loads(p.read_text())
        for p in (root / "cases").glob("*/result.json")
    }
    return manifest, records


def compose(root, case, record):
    folder = root / "cases" / case["id"] / "outputs"
    mf = folder / "layers.json"
    if not mf.exists():
        return None
    items = sorted(json.loads(mf.read_text())["layers"], key=lambda x: x["z_index"])
    base = Image.open(folder / items[0]["file"]).convert("RGBA")
    for item in items[1:]:
        x0, y0, x1, y1 = item["bounding_box"]["absolute"]
        crop = (
            Image.open(folder / item["file"])
            .convert("RGBA")
            .resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
        )
        base.alpha_composite(crop, (x0, y0))
    dest = root / "inspection" / f"{case['id']}-recomposed.png"
    base.save(dest)
    return base


def measurements(root, case, record):
    outputs = record.get("outputs", [])
    row = {
        "id": case["id"],
        "case": case["case"],
        "configuration": case["configuration"],
        "repeat": case.get("repeat", 1),
        "status": record["status"],
        "output_count": len(outputs),
        "api_ms": record.get("api_ms"),
        "end_to_end_ms": record.get("end_to_end_ms"),
    }
    if not outputs:
        return row
    folder = root / "cases" / case["id"] / "outputs"
    image = Image.open(folder / outputs[0]["file"])
    if case.get("edit_box"):
        source = (
            Image.open(root / "fixtures" / case["references"][0])
            .convert("RGB")
            .resize(image.size, Image.Resampling.LANCZOS)
        )
        mask = Image.new("L", image.size, 255)
        x0, y0, x1, y1 = case["edit_box"]
        ImageDraw.Draw(mask).rectangle(
            (
                round(x0 * image.width / 1000),
                round(y0 * image.height / 1000),
                round(x1 * image.width / 1000),
                round(y1 * image.height / 1000),
            ),
            fill=0,
        )
        diff = ImageChops.difference(source, image.convert("RGB"))
        row["outside_box_rgb_mae"] = sum(ImageStat.Stat(diff, mask).mean) / 3
    if case["case"] == "alpha-edit" and "A" in image.getbands():
        src = (
            Image.open(root / "fixtures" / case["references"][0])
            .convert("RGBA")
            .getchannel("A")
            .resize(image.size, Image.Resampling.LANCZOS)
            .point(lambda p: 255 if p > 127 else 0)
        )
        out = image.getchannel("A").point(lambda p: 255 if p > 127 else 0)
        intersection = sum(ImageChops.multiply(src, out).histogram()[1:])
        union = sum(ImageChops.lighter(src, out).histogram()[1:])
        row["alpha_silhouette_iou"] = intersection / union if union else 1
    recomposed = compose(root, case, record)
    if recomposed:
        source = (
            Image.open(root / "fixtures" / case["references"][0])
            .convert("RGB")
            .resize(recomposed.size, Image.Resampling.LANCZOS)
        )
        row["recomposition_rgb_mae"] = (
            sum(
                ImageStat.Stat(
                    ImageChops.difference(source, recomposed.convert("RGB"))
                ).mean
            )
            / 3
        )
    return row


def panel_image(path, size):
    source = Image.open(path).convert("RGBA")
    source.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "#e8e8e8")
    if source.getchannel("A").getextrema()[0] < 255:
        d = ImageDraw.Draw(canvas)
        for y in range(0, size[1], 20):
            for x in range(0, size[0], 20):
                if (x // 20 + y // 20) % 2:
                    d.rectangle((x, y, x + 19, y + 19), fill="#ffffff")
    canvas.paste(
        source, ((size[0] - source.width) // 2, (size[1] - source.height) // 2), source
    )
    return canvas


def boards(root, manifest, records):
    boarddir = root / "inspection"
    boarddir.mkdir(exist_ok=True)
    mapping = {}
    font = ImageFont.load_default(size=22)
    for name in sorted({c["case"] for c in manifest["cases"]}):
        group = [
            c
            for c in manifest["cases"]
            if c["case"] == name and records.get(c["id"], {}).get("status") == "success"
        ]
        if not group:
            continue
        random.Random(int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)).shuffle(
            group
        )
        w, h = 540, 600
        cols = min(3, len(group))
        rows = (len(group) + cols - 1) // cols
        canvas = Image.new("RGB", (cols * w, rows * h + 70), "#ffffff")
        draw = ImageDraw.Draw(canvas)
        draw.text((15, 12), name, fill="black", font=font)
        mapping[name] = {}
        for n, case in enumerate(group):
            label = chr(65 + n)
            mapping[name][label] = case["id"]
            record = records[case["id"]]
            folder = root / "cases" / case["id"] / "outputs"
            output = record["outputs"][0]["file"]
            recomposed = root / "inspection" / f"{case['id']}-recomposed.png"
            display = recomposed if recomposed.exists() else folder / output
            x = (n % cols) * w
            y = (n // cols) * h + 65
            canvas.paste(panel_image(display, (w - 16, h - 48)), (x + 8, y + 36))
            draw.text((x + 16, y), label, fill="black", font=font)
        canvas.save(boarddir / f"{name}.jpg", quality=94)
    (boarddir / "blind-mapping.json").write_text(json.dumps(mapping, indent=2))


def analyze(root):
    manifest, records = load(root)
    (root / "inspection").mkdir(exist_ok=True)
    rows = [
        measurements(root, c, records[c["id"]])
        for c in manifest["cases"]
        if c["id"] in records
    ]
    summary = {}
    for config in sorted({r["configuration"] for r in rows}):
        group = [r for r in rows if r["configuration"] == config]
        success = [r for r in group if r["status"] == "success"]
        summary[config] = {
            "planned": sum(c["configuration"] == config for c in manifest["cases"]),
            "journaled": len(group),
            "successful": len(success),
            "outputs": sum(r["output_count"] for r in group),
            "api_median_ms": statistics.median(r["api_ms"] for r in success)
            if success
            else None,
        }
    (root / "measurements.json").write_text(
        json.dumps({"summary": summary, "cases": rows}, indent=2)
    )
    boards(root, manifest, records)
    print(json.dumps(summary, indent=2))


def observed_cost(case, record):
    """2026-10-25 public-list estimate; unknown submission cost stays unknown."""
    if record["status"] != "success":
        return None
    if case["model"] == "flash":
        return round(len(record.get("outputs", [])) * 0.12, 2)
    cost = 0.0
    for output in record.get("outputs", []):
        width, height = output["size"]
        low_tier = width * height <= 2_610_000
        cost += (
            (0.15 if low_tier else 0.30)
            if case["command"] == "decompose"
            else (0.30 if low_tier else 0.60)
        )
    cost += max(0, len(case["references"]) - 1) * 0.02
    return round(cost, 2)


def public_request(request):
    allowed = (
        "model",
        "prompt",
        "size",
        "output_format",
        "background",
        "layer_decomposition",
        "optimize_prompt_options",
    )
    return {key: request[key] for key in allowed if key in request}


def accounting(rows):
    return {
        "planned_requests": len(rows),
        "submitted_requests": sum(row.get("generation_attempts", 0) for row in rows),
        "successful_requests": sum(row["status"] == "success" for row in rows),
        "outputs": sum(len(row.get("outputs", [])) for row in rows),
        "statuses": dict(Counter(row["status"] for row in rows)),
        "observed_output_list_cost_cny": round(
            sum(row.get("list_cost_cny") or 0 for row in rows), 2
        ),
        "unknown_cost_present": any(
            row.get("generation_attempts", 0) and row.get("list_cost_cny") is None
            for row in rows
        ),
    }


def public_study(root):
    manifest, records = load(root)
    metrics = {
        row["id"]: row
        for row in json.loads((root / "measurements.json").read_text())["cases"]
    }
    review_file = root / "reviewed-results.json"
    reviews = json.loads(review_file.read_text()) if review_file.exists() else {}
    definitions, prompts, results = {}, {}, []
    output_fields = (
        "file",
        "size",
        "format",
        "mode",
        "bytes",
        "sha256",
        "alpha_extrema",
        "fully_transparent_fraction",
        "nonopaque_fraction",
    )
    for case in manifest["cases"]:
        key = case["case"] + "/" + case.get("variant", "baseline")
        definitions[key] = {
            field: case[field]
            for field in (
                "case",
                "variant",
                "category",
                "command",
                "prompt",
                "size",
                "references",
                "criteria",
                "required_text",
                "forbidden_text",
                "background",
                "marker_rect",
                "marker_alpha",
                "edit_box",
                "hypothesis",
            )
            if field in case
        }
        record = records.get(
            case["id"], {"status": "not_run", "generation_attempts": 0}
        )
        row = {
            "id": case["id"],
            "definition": key,
            "model": case["model"],
            "configuration": case["configuration"],
            "repeat": case.get("repeat", 1),
            "status": record["status"],
            "generation_attempts": record.get("generation_attempts", 0),
        }
        for field in (
            "api_ms",
            "end_to_end_ms",
            "error_code",
            "http_status",
            "usage",
            "script_sha256",
        ):
            if field in record:
                row[field] = record[field]
        request = public_request(record.get("request", {}))
        if "prompt" in request:
            prompt = request.pop("prompt")
            digest = hashlib.sha256(prompt.encode()).hexdigest()
            prompts[digest] = prompt
            request["prompt_sha256"] = digest
        row["request"] = request
        row["outputs"] = [
            {field: image[field] for field in output_fields if field in image}
            for image in record.get("outputs", [])
        ]
        row["measurements"] = {
            field: metrics[case["id"]][field]
            for field in (
                "outside_box_rgb_mae",
                "alpha_silhouette_iou",
                "recomposition_rgb_mae",
            )
            if field in metrics.get(case["id"], {})
        }
        row["review"] = reviews.get(case["id"])
        row["list_cost_cny"] = observed_cost(case, record)
        layer_file = root / "cases" / case["id"] / "outputs/layers.json"
        if layer_file.exists():
            row["layers"] = [
                {
                    field: layer[field]
                    for field in (
                        "file",
                        "z_index",
                        "output_format",
                        "size",
                        "reported_size",
                        "bounding_box",
                        "name",
                        "description",
                    )
                    if field in layer
                }
                for layer in json.loads(layer_file.read_text())["layers"]
            ]
        results.append(row)
    return {
        "study": manifest["study"],
        "manifest_sha256": hashlib.sha256(
            (root / "cases.json").read_bytes()
        ).hexdigest(),
        "fixtures": manifest["fixtures"],
        "definitions": definitions,
        "submitted_prompts": prompts,
        "summary": accounting(results),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+")
    parser.add_argument(
        "--export", help="Write the explicit public summary after analyzing every root."
    )
    args = parser.parse_args()
    roots = [Path(root).expanduser().resolve() for root in args.roots]
    for root in roots:
        analyze(root)
    if args.export:
        studies = [public_study(root) for root in roots]
        result = {
            "checked_on": "2026-10-25",
            "pricing_source": "https://www.volcengine.com/docs/ark/model-pricing",
            "cost_note": "Public-list estimate from observed outputs and Pro extra references, not an account invoice.",
            "review_note": "Case-specific 0/1/2 criteria, model labels hidden during self-review; not independent human blind assessment or a population model ranking.",
            "summary": accounting(
                [row for study in studies for row in study["results"]]
            ),
            "studies": studies,
        }
        Path(args.export).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
