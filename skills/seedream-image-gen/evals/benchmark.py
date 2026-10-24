#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27.0", "pillow>=10.1.0"]
# ///
"""Prepare or execute the bounded Pro/Flash study; never replay an existing case.

Run from a directory containing the usual .env, or export ARK_API_KEY.
Preparation is free. --execute explicitly permits up to the 16 manifest cases.
Outputs, journals and generated pictures belong outside the skill repository.
"""

import argparse
import asyncio
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random
import sys
import time

import httpx
from PIL import Image, ImageDraw, ImageFont


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seedream_image_gen.py"


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def prepare(root):
    root.mkdir(parents=True, exist_ok=True)
    fixtures = root / "fixtures"
    existing = root / "cases.json"
    if existing.exists():
        saved = json.loads(existing.read_text())
        cases = saved.get("cases", [])
        identifiers = [case.get("id", "") for case in cases]
        if len(cases) != 16 or len(set(identifiers)) != 16 or any(
            not name or Path(name).name != name or name in {".", ".."} for name in identifiers
        ):
            raise SystemExit("Invalid existing study manifest; use a new output directory.")
        expected_files = {"objects.png", "palette.png", "alpha-cup.png"}
        if set(saved.get("fixtures", {})) != expected_files:
            raise SystemExit("Existing study has unexpected references; preserve it and use a new directory.")
        for name, expected_hash in saved["fixtures"].items():
            path = fixtures / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
                raise SystemExit("Existing reference differs from its recorded hash; it has been preserved.")
        return saved  # A previous study is immutable, even after runner/Pillow upgrades.
    fixtures.mkdir(exist_ok=True)
    source = Image.new("RGB", (1024, 1024), "#fff4df")
    draw = ImageDraw.Draw(source)
    draw.text((100, 80), "NOVA", fill="#203344", font=ImageFont.load_default(size=100))
    draw.rounded_rectangle((130, 400, 430, 760), 40, fill="#d64035")
    draw.ellipse((355, 470, 550, 680), outline="#d64035", width=40)
    draw.rounded_rectangle((650, 470, 850, 820), 45, fill="#207a85")
    draw.ellipse((680, 350, 820, 590), fill="#e6af32")
    source.save(fixtures / "objects.png")
    palette = Image.new("RGB", (1024, 1024), "#f9edce")
    ImageDraw.Draw(palette).rectangle((200, 200, 824, 824), fill="#159b91")
    palette.save(fixtures / "palette.png")
    alpha = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(alpha)
    draw.rounded_rectangle((190, 240, 700, 830), 80, fill="#159b91")
    draw.ellipse((550, 380, 900, 720), outline="#159b91", width=60)
    alpha.save(fixtures / "alpha-cup.png")
    core = [
        ("text", "generate", "横版16:9科技海报，奶油白背景配青绿色几何图形。顶部大号黑色无衬线标题准确写“新绿计划”，副标题“更少等待，更多创作”。下方三个等宽卡片分别写“文生图”“精准编辑”“透明图层”。留白充足，文字清晰，不增加其他文字或水印。", "2K", []),
        ("small-banner", "generate", "横向产品宣传图，一只青绿色陶瓷手冲咖啡壶位于画面右侧，柔和的窗边自然光，暖米色桌面，左侧60%为干净留白，真实产品摄影。不要人物、文字、品牌、标志或水印。", "1500x600", []),
        ("coordinate-edit", "edit", "把图1 <bbox>100 350 550 780</bbox> 中左侧红色杯子改为深蓝色，保持杯子形状、把手、右侧花瓶、顶部NOVA文字和背景不变，保持原来的扁平矢量画风。", "1.5K", ["objects.png"]),
        ("multi-reference", "generate", "参考图1中左侧杯子的外形和把手，使用图2中央的青绿色作为杯子颜色、图2周围的暖米色作为背景。只画一个杯子，居中放置，保持扁平矢量风格，不画花瓶，不加文字或水印。", "1.5K", ["objects.png", "palette.png"]),
    ]
    cases = []
    configs = [("pro-standard", "pro", "standard"), ("pro-fast", "pro", "fast"), ("flash-standard", "flash", "standard")]
    for label, command, prompt, size, references in core:
        for config, model, mode in configs:
            cases.append(dict(id=f"{label}-{config}", case=label, command=command, prompt=prompt,
                              size=size, references=references, configuration=config, model=model, mode=mode))
    random.Random(20261024).shuffle(cases)
    # First smoke pair exercises both models; the remaining order stays fixed.
    smoke_ids = ["text-flash-standard", "text-pro-standard"]
    cases = [next(case for case in cases if case["id"] == name) for name in smoke_ids] + [case for case in cases if case["id"] not in smoke_ids]
    for model in ("pro", "flash"):
        cases.append(dict(id=f"alpha-edit-{model}", case="alpha-edit", command="edit", model=model,
                          mode="standard", configuration=f"{model}-standard", size="1.5K",
                          references=["alpha-cup.png"], background="transparent",
                          prompt="把杯子改成橙黄色，保持杯子的外形和把手不变，保持透明背景，不增加其他物体、文字或水印。"))
        cases.append(dict(id=f"decompose-{model}", case="decompose", command="decompose", model=model,
                          mode="standard", configuration=f"{model}-standard", size="1.5K",
                          references=["objects.png"],
                          prompt="只拆出图1 <bbox>100 350 550 780</bbox> 中的红色杯子和 <bbox>80 60 500 220</bbox> 中的NOVA标题文字，分别成为两个独立的透明图层；其余内容保留在底图。"))
    manifest = {"study": "seedream-pro-flash-20261024", "max_requests": 16, "cases": cases,
                "fixtures": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in fixtures.glob("*.png")}}
    write_json(existing, manifest)
    return manifest


def inspect_outputs(folder):
    outputs = []
    for path in sorted(folder.glob("*")):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        with Image.open(path) as image:
            record = dict(file=path.name, size=list(image.size), format=image.format, mode=image.mode,
                          bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            if "A" in image.getbands():
                histogram = image.getchannel("A").histogram()
                pixels = image.width * image.height
                record.update(alpha_extrema=list(image.getchannel("A").getextrema()),
                              fully_transparent_fraction=histogram[0] / pixels,
                              nonopaque_fraction=1 - histogram[255] / pixels)
            outputs.append(record)
    return outputs


def worker(root, case):
    spec = importlib.util.spec_from_file_location("seedream_benchmark", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    folder = root / "cases" / case["id"]
    folder.mkdir(parents=True, exist_ok=True)
    journal = folder / "result.json"
    if journal.exists():
        raise SystemExit("Case already has a journal; never automatically replay it.")
    result = dict(id=case["id"], case=case["case"], configuration=case["configuration"],
                  model=case["model"], status="prepared", generation_attempts=0,
                  script_sha256=hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
    write_json(journal, result)

    async def once(api_key, base_url, body, timeout):
        result.update(status="submitted", generation_attempts=1,
                      request={key: body[key] for key in ("model", "prompt", "size", "output_format", "background", "layer_decomposition", "optimize_prompt_options") if key in body},
                      reference_count=len(case["references"]))
        write_json(journal, result)  # Durable before sending; interrupted cases are not replayed.
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
                response = await module._generate_single(client, body, timeout)
            result.update(status="response_received", api_ms=response[4],
                          usage={key: response[2][key] for key in ("generated_images", "input_images", "output_tokens", "total_tokens") if response[2] and key in response[2]})
            write_json(journal, result)
            return response
        except (httpx.TimeoutException, httpx.TransportError):
            result.update(status="outcome_unknown", error_code="TransportOutcomeUnknown")
            write_json(journal, result)
            raise module._APIError(0, "OutcomeUnknown", "No automatic replay of an uncertain paid request.")
        except module._APIError as error:
            result.update(status="download_failed" if error.code == "DownloadFailed" else "api_error",
                          error_code=error.code, http_status=error.status_code)
            write_json(journal, result)
            raise

    module._generate_with_retry = once
    arguments = [str(SCRIPT), case["command"], "--model", case["model"], "--prompt", case["prompt"],
                 "--size", case["size"], "--optimize-prompt", case["mode"], "--output-format", "png",
                 "--out-dir", str(folder / "outputs"), "--timeout", "300"]
    if case["command"] != "decompose":
        arguments += ["--no-negative-prompt"]
    if case.get("background"):
        arguments += ["--background", case["background"]]
    for reference in case["references"]:
        arguments += ["--reference-image", str(root / "fixtures" / reference)]
    stdout, stderr = io.StringIO(), io.StringIO()
    started = time.monotonic()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            sys.argv = arguments
            try:
                status = module.main()
            except SystemExit as error:
                status = error.code
        result["exit_code"] = status
        if status == 0:
            result["status"] = "success"
        elif result["generation_attempts"] == 0:
            result.update(status="not_submitted", error_code="MissingCredentials" if "ARK_API_KEY is required" in stderr.getvalue() else "ClientValidation")
    except Exception as error:
        result.update(status="client_failure_after_response" if result["status"] == "response_received" else "outcome_unknown",
                      error_code=error.__class__.__name__)
    result.update(end_to_end_ms=round((time.monotonic() - started) * 1000),
                  outputs=inspect_outputs(folder / "outputs"))
    if (folder / "outputs/layers.json").exists():
        result["layer_manifest"] = f"cases/{case['id']}/outputs/layers.json"
    write_json(journal, result)
    print(json.dumps({key: result.get(key) for key in ("id", "status", "api_ms", "end_to_end_ms", "error_code")}, ensure_ascii=False), flush=True)


async def execute(root, cases, concurrency):
    semaphore = asyncio.Semaphore(concurrency)
    stop_for_credentials = False

    async def run(case):
        nonlocal stop_for_credentials
        async with semaphore:
            journal = root / "cases" / case["id"] / "result.json"
            if stop_for_credentials or journal.exists():
                return
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(Path(__file__).resolve()), "--out-dir", str(root), "--worker", case["id"],
                stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            out, _error = await process.communicate()
            if out:
                print(out.decode().strip(), flush=True)
            if journal.exists():
                result = json.loads(journal.read_text())
                stop_for_credentials |= result.get("error_code") == "MissingCredentials"
            elif process.returncode:
                print(json.dumps({"id": case["id"], "status": "worker_failed_before_journal"}), flush=True)

    await asyncio.gather(*(run(case) for case in cases))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--limit", type=int, default=16)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = Path(args.out_dir).expanduser().resolve()
    if args.worker:
        manifest = json.loads((root / "cases.json").read_text())
        worker(root, next(case for case in manifest["cases"] if case["id"] == args.worker))
        return
    if not 1 <= args.limit <= 16 or args.concurrency < 1:
        parser.error("Use a limit of 1–16 and positive concurrency.")
    manifest = prepare(root)
    if args.execute:
        asyncio.run(execute(root, manifest["cases"][:args.limit], args.concurrency))
    results = [json.loads(path.read_text()) for path in sorted((root / "cases").glob("*/result.json"))]
    write_json(root / "benchmark-results.json", {"study": manifest["study"], "results": results})
    print(f"Prepared {len(manifest['cases'])} cases; {len(results)} cases have journals. Existing cases are never resubmitted.")


if __name__ == "__main__":
    main()
