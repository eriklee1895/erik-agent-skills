#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27", "pillow>=10", "numpy>=2"]
# ///
"""Live, resumable Ark benchmark. Paid calls require --run. No keys/URLs in results.

uv run evals/seedream55_benchmark.py --run --out-dir /absolute/private/results
Successful AND failed jobs are preserved; remove a failed job directory deliberately
before a repeat. A transport error never automatically replays a paid submission.
"""
import argparse
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from PIL import Image, ImageDraw, ImageFont
import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'seedream_image_gen.py'
SPEC = importlib.util.spec_from_file_location('seedream_benchmark_client', SCRIPT)
sg = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sg
SPEC.loader.exec_module(sg)
MODELS = {'55': sg.MODEL_55, 'pro': sg.MODEL_PRO}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def fixture(root, font_path=None):
    path = root / 'fixture.png'
    if path.exists():
        return path
    image = Image.new('RGB', (1536, 1024), '#F7F2E8')
    d = ImageDraw.Draw(image)
    # These fonts are fixture-authoring dependencies only, not skill runtime requirements.
    font_path = font_path or '/System/Library/Fonts/Supplemental/Arial.ttf'
    font = ImageFont.truetype(font_path, 92) if Path(font_path).is_file() else ImageFont.load_default(size=92)
    small = ImageFont.truetype(font_path, 38) if Path(font_path).is_file() else ImageFont.load_default(size=38)
    d.text((90, 65), 'GREEN STUDIO', font=font, fill='#173E36')
    for y, text in [(215, 'OPEN DAY 2026'), (280, 'NOV 20 | 10:00-18:00'), (345, 'TICKET: 128 CNY')]:
        d.text((95, y), text, font=small, fill='#173E36')
    d.rounded_rectangle((100, 500, 500, 900), radius=45, fill='#D4513F')
    d.ellipse((540, 520, 880, 860), fill='#E9BC47')
    d.rectangle((1000, 500, 1370, 900), fill='#2B7585')
    d.text((1065, 650), 'ARK 55', font=small, fill='white')
    image.save(path)
    return path


async def main(args):
    root = Path(args.out_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    sg._load_dotenv()
    key, base = sg._get_api_settings()
    gate = asyncio.Semaphore(args.concurrency)

    async def run(name, model='55', prompt='', refs=(), size='2K', background='opaque', layers=None):
        folder = root / name
        folder.mkdir(exist_ok=True)
        result_path = folder / 'result.json'
        if result_path.exists():
            return json.loads(result_path.read_text())
        body = {'model': MODELS[model], 'size': size, 'output_format': 'png', 'watermark': False,
                'optimize_prompt_options': {'mode': 'standard'}}
        if prompt:
            body['prompt'] = prompt
        if refs:
            body['image'] = [sg._encode_reference(str(p)) for p in refs]
            if len(refs) == 1:
                body['image'] = body['image'][0]
        if layers is None:
            body['background'] = background
        else:
            body['layer_decomposition'] = True
            if model == '55':
                body['layer_decomposition_options'] = layers
        record = {k: v for k, v in body.items() if k != 'image'}
        record.update(name=name, references=[{'file': str(p.relative_to(root)),
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in refs])
        write_json(folder / 'request.json', record)
        async with gate:
            print('START', name, flush=True)
            # Persist in-flight state before submission so interruption cannot silently replay.
            write_json(result_path, {'name': name, 'status': 'outcome_unknown', 'model': MODELS[model]})
            t0 = time.monotonic()
            try:
                assets, revised, usage, reported, api_ms = await sg._generate_with_retry(key, base, body, args.timeout)
                items = []
                for i, asset in enumerate(assets):
                    path = folder / f'asset-{i:03d}.png'
                    path.write_bytes(asset.content)
                    with Image.open(path) as im:
                        a = np.asarray(im.convert('RGBA').getchannel('A'))
                        item = {'file': str(path.relative_to(root)), 'size': list(im.size), 'mode': im.mode,
                                'sha256': hashlib.sha256(asset.content).hexdigest(),
                                'alpha_zero_fraction': float(np.mean(a == 0)),
                                'alpha_partial_fraction': float(np.mean((a > 0) & (a < 255)))}
                    item.update({f: getattr(asset, f) for f in ('z_index', 'bounding_box', 'name', 'description',
                                 'text_recognition', 'background') if getattr(asset, f) is not None})
                    items.append(item)
                result = {'name': name, 'status': 'ok', 'model': MODELS[model], 'api_ms': api_ms,
                          'elapsed_ms': round((time.monotonic()-t0)*1000), 'usage': usage, 'assets': items}
            except sg._APIError as e:
                result = {'name': name, 'status': 'error', 'model': MODELS[model], 'code': e.code,
                          'http_status': e.status_code, 'elapsed_ms': round((time.monotonic()-t0)*1000)}
            write_json(result_path, result)
            print('DONE', name, result['status'], result['elapsed_ms'], flush=True)
            return result

    f = fixture(root, args.fixture_font)
    product_prompt = '正方形专业产品静物摄影：左侧一只红色陶瓷马克杯，右侧一只蓝色玻璃花瓶插一枝白色雏菊，中间一个黄色柠檬。米白背景和木质桌面，柔和左侧窗光，材质真实，比例准确。左侧杯子位于画面横向10%至45%、纵向40%至85%范围。不要文字，不要其他物件。'
    product = await run('source-product', prompt=product_prompt, size='1024x1024')
    if product['status'] != 'ok':
        raise SystemExit('Source failed; results preserved, no automatic rerun.')
    source = root / product['assets'][0]['file']

    async def chain(model, kind, rounds):
        previous = source if kind == 'product' else f
        colors = ['深蓝色', '橙黄色', '墨绿色', '紫色', '白色', '红色']
        titles = ['BLUE STUDIO', 'GOLD STUDIO', 'NOVA STUDIO', 'OPEN STUDIO', 'ERIK STUDIO', 'GREEN STUDIO']
        for index in range(rounds):
            if kind == 'product':
                prompt = f'只把图1 <bbox>50 300 520 950</bbox> 中左侧马克杯的杯身和把手改为{colors[index % 6]}。严格保持杯子形状、右侧蓝色花瓶、白色雏菊、柠檬、桌面、背景、光影和构图不变。'
                size = '1024x1024'
            else:
                prompt = f'只把图1顶部标题“{titles[index-1] if index else "GREEN STUDIO"}”替换为“{titles[index]}”。保持字体、字号、标题位置、全部小字、三个几何图形、颜色和背景不变。'
                size = '1536x1024'
            r = await run(f'edit-{kind}-{model}-{index+1:02d}', model, prompt, [previous], size)
            if r['status'] != 'ok':
                break
            previous = root / r['assets'][0]['file']

    typography = [
        ('cn', '横版1536:1024奶油白极简茶叶海报，深绿色大标题准确写“桂馥茶集”，副标题“冬日暖茶，第二杯半价”。小字分四行逐字准确写：“净含量：250克”“配料：云南红茶、桂花”“活动日期：2026.11.20—11.30”“门店地址：上海市静安区新绿路128号”。右侧一杯热茶，清晰中文，严谨留白。'),
        ('multi', '横版奶油白专业咖啡海报，黑色无衬线字，大标题“ORIGIN COFFEE”。下面四行文案分别为：“云南保山 · 250 g”“Café recién tostado”“ダークチョコレート”“خصم 20٪ اليوم”。底部小字“18 g → 36 g | 92°C | 28 s”。左侧咖啡豆包装，全部文字准确且清晰，不添加其他文字。'),
        ('dense', '制作横版极简实验室说明卡，白底深蓝无衬线字。标题“ARK LAB 2026”。下方整齐排六行文字：“Batch: A55-261028”“Voltage: 12.5 V ± 0.2 V”“Temperature: 23.0 °C”“浓度：0.85%（质量分数）”“保质期：2026-11-14 至 2027-11-13”“注意：避光密封保存，勿冷冻”。右侧一支透明玻璃试剂瓶，文字无遗漏，不添文字。')]
    async def refined_poster_chain():
        previous = f
        titles = ['BLUE STUDIO', 'GOLD STUDIO', 'NOVA STUDIO', 'OPEN STUDIO', 'ERIK STUDIO', 'GREEN STUDIO']
        for index, title in enumerate(titles):
            old = titles[index-1] if index else 'GREEN STUDIO'
            prompt = f'只修改图1 <bbox>58 64 512 175</bbox> 内的标题，把“{old}”改成“{title}”。严格保持文字原来的左上角位置、字号、颜色和字体。框外所有像素保持原样，不调整布局、不增加纹理、不移动色块、不改变留白，保持1536×1024画布。'
            rec = await run(f'edit-poster-refined-55-{index+1:02d}', prompt=prompt, refs=[previous], size='1536x1024')
            if rec['status'] != 'ok':
                break
            previous = root / rec['assets'][0]['file']

    jobs = [refined_poster_chain()]
    jobs += [chain(m, k, n) for m in MODELS for k, n in [('product', 12), ('poster', 6)]]
    for m in MODELS:
        for kind, prompt in typography:
            for rep in range(2):
                jobs.append(run(f'type-{kind}-{m}-{rep+1}', m, prompt, size='1536x1024'))
        jobs.append(run(f'fusion-{m}', m, '图1左侧的马克杯和右侧花瓶一起放进图2海报右下角。保持图1的产品颜色、材质、比例，保持图2所有文字、背景和几何图形，产品自然融合，透视和光照统一。', [source, f], '1536x1024'))
    jobs += [
        run('rgba-solid', prompt='独立的红色陶瓷茶壶产品素材，完整壶嘴与把手，真实柔和半透明接触投影，主体之外完全透明，不要场景，不要文字。', background='transparent', size='1K'),
        run('rgba-glass', prompt='独立透明玻璃水杯，薄玻璃边缘和清水，杯身中央可透过下方背景，真实半透明折射和柔和投影，主体之外完全透明，不要白底或棋盘格。', background='transparent', size='1K'),
        run('rgba-logo', prompt='独立文字标志“新绿 STUDIO”，深绿色无衬线字体和一片叶子，文字与叶子之外完全透明，边缘清楚，不要投影，不要其他文字。', background='transparent', size='1K'),
        run('rgba-from-rgb', prompt='只提取图1左侧的红色马克杯，完整保留杯身与把手、颜色和材质，移除花瓶、柠檬、桌面及背景，杯子以外完全透明。', refs=[source], background='transparent', size='1K'),
        run('rgba-multi-reference', prompt='提取图1红色杯子和蓝色花瓶，以及图2的红色圆角矩形、黄色圆形和蓝色矩形，在同一张透明画布中独立摆放，互不重叠，保留原颜色和形状，不要文字。', refs=[source, f], background='transparent', size='1K'),
        run('layers-poster-6', refs=[f], size='auto', layers={'max_images': 6, 'text_recognition': True}),
        run('layers-poster-20', refs=[f], size='auto', layers={'max_images': 20, 'text_recognition': True}),
        run('layers-product', refs=[source], size='auto', layers={'max_images': 10, 'text_recognition': True}),
        run('layers-pro-poster', model='pro', refs=[f], size='auto', layers={}),
    ]
    # Extension cases: 2K text, realism, alpha auto and >16-layer behavior.
    crowded = root / 'crowded.png'
    if not crowded.exists():
        canvas = Image.new('RGB', (1536, 1536), '#F3EFE5')
        draw = ImageDraw.Draw(canvas)
        for i in range(25):
            x, y = 45 + (i % 5) * 300, 45 + (i // 5) * 300
            hue = (i * 47 % 200 + 30, i * 83 % 200 + 30, i * 113 % 200 + 30)
            draw.rounded_rectangle((x, y, x+220, y+220), radius=15+i*3, fill=hue)
        canvas.save(crowded)
    for model in MODELS:
        jobs.append(run(f'type-cn-2K-{model}', model, typography[0][1], size='2K'))
        jobs.append(run(f'realism-portrait-{model}', model,
            '纪实摄影，一位40岁左右的东亚女性咖啡师，站在有自然窗光的咖啡馆吧台后，双手轻握一只白色陶瓷杯，真实皮肤毛孔、细纹、手指结构和亚麻围裙纹理，温暖克制，50mm镜头，横版，背景不出现文字。', size='1536x1024'))
        jobs.append(run(f'realism-material-{model}', model,
            '专业产品摄影，亚麻桌布上一只拉丝不锈钢手冲壶、一只盛清水的透明玻璃杯与一只橙黄色陶瓷小碟，柔和左侧窗光，真实金属反射、玻璃折射、清水液面及织物纹理，透视协调，横版，无文字。', size='1536x1024'))
    jobs.extend([
        run('edit-poster-bbox-55', prompt='只修改图1 <bbox>58 64 512 175</bbox> 内的标题，把“GREEN STUDIO”改成“BLUE STUDIO”。严格保持文字原来的左上角位置、字号、颜色和字体。框外所有像素保持原样，不调整布局、不增加纹理、不移动色块、不改变留白，保持1536×1024画布。', refs=[f], size='1536x1024'),
        run('edit-poster-english-55', prompt='Edit only the top title: replace "GREEN STUDIO" with "BLUE STUDIO". Keep the title at its original position and retain its font, size and color. Preserve every other pixel exactly, including all small text, the red rounded rectangle, yellow circle and blue rectangle. Do not redesign, recenter, add texture, or change the canvas layout.', refs=[f], size='1536x1024'),
        run('rgba-auto', prompt='一片独立绿色树叶，主体以外完全透明，没有文字或背景。', size='1K', background='auto'),
        run('layers-crowded', prompt='把25个彩色圆角矩形分别拆成独立透明图层，每个色块单独一层，不要合并成行或整幅图；保留原位置、颜色与形状。',
            refs=[crowded], size='1K', layers={'max_images': 40, 'text_recognition': True}),
    ])
    await asyncio.gather(*jobs)
    records = [json.loads(p.read_text()) for p in sorted(root.glob('*/result.json'))]
    write_json(root / 'results.json', {'models': MODELS, 'records': records})
    print('RESULTS', root / 'results.json', len(records), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Authorize paid live requests.')
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--concurrency', type=int, default=4)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--fixture-font', help='Optional font file for the deterministic Latin fixture; Arial on macOS or Pillow fallback.')
    args = parser.parse_args()
    if not args.run:
        parser.error('Pass --run to execute paid live requests.')
    asyncio.run(main(args))
