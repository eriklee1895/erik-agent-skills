#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=10", "numpy>=2"]
# ///
"""Analyze saved benchmark artifacts without network calls or model-based grading."""
import argparse
import json
import math
from pathlib import Path
import statistics

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def image_rgb(path, size=None):
    with Image.open(path) as im:
        rgb = im.convert('RGB')
        if size and rgb.size != size:
            rgb = rgb.resize(size, Image.Resampling.LANCZOS)
        return np.asarray(rgb, dtype=np.float32)


def difference(a, b, mask=None):
    delta = b - a
    if mask is not None:
        delta = delta[mask]
    channel_max = np.max(np.abs(delta), axis=-1)
    mse = float(np.mean(delta ** 2))
    return {'mae': float(np.mean(np.abs(delta))), 'mean_signed_delta': float(np.mean(delta)),
            'changed_gt8_fraction': float(np.mean(channel_max > 8)),
            'changed_gt32_fraction': float(np.mean(channel_max > 32)),
            'exact_pixel_fraction': float(np.mean(channel_max == 0)),
            'psnr_db': 10 * math.log10(255**2 / mse) if mse else None}


def compose(root, record, omit=()):
    assets = sorted(record['assets'], key=lambda x: x['z_index'])
    base = Image.open(root / assets[0]['file']).convert('RGBA')
    for layer in assets[1:]:
        if layer['z_index'] in omit:
            continue
        box = layer.get('bounding_box', {}).get('absolute')
        if not box:
            raise ValueError(f"Missing bbox for {record['name']} / {layer['z_index']}")
        l, t, r, b = box
        crop = Image.open(root / layer['file']).convert('RGBA').resize((r-l, b-t), Image.Resampling.LANCZOS)
        base.alpha_composite(crop, (l, t))
    return base


def sheet(root, names, output, width=440, columns=3, checker=False):
    cells = []
    for name in names:
        paths = sorted((root / name).glob('asset-*.png'))
        if not paths:
            continue
        im = Image.open(paths[0]).convert('RGBA')
        im.thumbnail((width, width), Image.Resampling.LANCZOS)
        cell = Image.new('RGB', (width, width+38), '#E7E8EC')
        if checker:
            d = ImageDraw.Draw(cell)
            for y in range(0,width,22):
                for x in range(0,width,22):
                    d.rectangle((x,y,x+21,y+21), fill=('#2D3447' if (x//22+y//22)%2 else '#B7BCC8'))
        cell.paste(im, ((width-im.width)//2, (width-im.height)//2), im)
        ImageDraw.Draw(cell).text((10,width+10),name,fill='black')
        cells.append(cell)
    if not cells:
        return
    result = Image.new('RGB',(columns*width,math.ceil(len(cells)/columns)*(width+38)), 'white')
    for i, cell in enumerate(cells): result.paste(cell,((i%columns)*width,(i//columns)*(width+38)))
    result.save(output)


def main(root, localization_font=None):
    records = [json.loads(p.read_text()) for p in sorted(root.glob('*/result.json'))]
    success = [r for r in records if r['status'] == 'ok']
    summary = {'request_count':len(records), 'success_count':len(success),
               'output_count':sum(len(r['assets']) for r in success), 'latency':{}, 'chains':{}, 'layers':[], 'rgba':[], 'cost':{}}
    for model in ('55','pro'):
        mid = 'doubao-seedream-5-5-261028' if model == '55' else 'doubao-seedream-5-0-pro-260628'
        subset = [r for r in success if r['model'] == mid]
        summary['latency'][model] = {'count':len(subset), 'api_median_ms':statistics.median(r['api_ms'] for r in subset) if subset else None}
        cost = 0
        for rec in subset:
            request = json.loads((root / rec['name'] / 'request.json').read_text())
            refs = len(request['references'])
            cost += refs * .05 if model == '55' else max(0, refs-1) * .02
            for a in rec['assets']:
                low = a['size'][0] * a['size'][1] <= 2_610_000
                cost += (.13 if low else .23) if model == '55' else ((.15 if low else .30) if request.get('layer_decomposition') else (.30 if low else .60))
        summary['cost'][model] = round(cost, 4)
        for kind in ('product','poster'):
            original = root / ('source-product/asset-000.png' if kind == 'product' else 'fixture.png')
            if not original.exists():
                summary['chains'][f'{kind}-{model}'] = {'rounds': [], 'source_missing': True}
                continue
            with Image.open(original) as im: size = im.size
            original_array = image_rgb(original)
            mask = np.ones((size[1],size[0]), dtype=bool)
            # Predeclared conservative protected-region masks; no model-derived segmentation.
            roi = (.05,.30,.62,.95) if kind == 'product' else (.02,.02,.98,.20)
            l,t,r,b = [round(v*extent) for v,extent in zip(roi,(size[0],size[1],size[0],size[1]))]
            mask[t:b,l:r] = False
            previous = original_array
            rounds = []
            for rec in sorted((r for r in success if r['name'].startswith(f'edit-{kind}-{model}-')),key=lambda r:r['name']):
                a=rec['assets'][0]
                current=image_rgb(root/a['file'],size)
                rounds.append({'name':rec['name'], 'resized_for_comparison':a['size'] != list(size),
                               'previous':difference(previous,current,mask), 'original':difference(original_array,current,mask),
                               'api_ms':rec['api_ms']})
                previous=current
            summary['chains'][f'{kind}-{model}']={'protected_mask_excluded_normalized':roi,'rounds':rounds}
    summary['edit_controls'] = []
    fixture = image_rgb(root/'fixture.png')
    mask = np.ones(fixture.shape[:2],dtype=bool)
    w,h=fixture.shape[1],fixture.shape[0]
    mask[round(.02*h):round(.20*h),round(.02*w):round(.98*w)] = False
    for rec in success:
        if rec['name'].startswith(('edit-poster-bbox-', 'edit-poster-english-', 'edit-poster-refined-')):
            arr = image_rgb(root/rec['assets'][0]['file'],(fixture.shape[1],fixture.shape[0]))
            summary['edit_controls'].append({'name':rec['name'],'protected_vs_original':difference(fixture,arr,mask),'api_ms':rec['api_ms']})
    for rec in success:
        request=json.loads((root/rec['name']/'request.json').read_text())
        if rec['name'].startswith('rgba-'):
            summary['rgba'].append({'name':rec['name'], **{k:rec['assets'][0][k] for k in ('size','mode','alpha_zero_fraction','alpha_partial_fraction')}})
        if request.get('layer_decomposition'):
            composed=compose(root,rec)
            output=root/rec['name']/'recomposed.png'
            composed.save(output)
            source=root/request['references'][0]['file']
            orig=image_rgb(source,composed.size)
            metrics=difference(orig,np.asarray(composed.convert('RGB'),dtype=np.float32))
            summary['layers'].append({'name':rec['name'],'output_count':len(rec['assets']), 'api_ms':rec['api_ms'],
                'base_size':list(composed.size),'source_resized_for_comparison':list(Image.open(source).size)!=list(composed.size),
                'recomposition':metrics,'ocr':[{'z_index':a['z_index'],**a['text_recognition']} for a in rec['assets'] if a.get('text_recognition')]})
    for kind in ('cn','multi','dense'):
        sheet(root,[f'type-{kind}-{m}-{i}' for i in (1,2) for m in ('55','pro')],root/f'typography-{kind}.jpg',width=768,columns=2)
    sheet(root,['source-product']+[f'edit-product-{m}-{i:02d}' for i in (1,6,12) for m in ('55','pro')],root/'editing.jpg',width=440)
    sheet(root,[r['name'] for r in success if r['name'].startswith('rgba-')],root/'transparency.jpg',checker=True)
    sheet(root,['realism-portrait-55','realism-portrait-pro','realism-material-55','realism-material-pro','fusion-55','fusion-pro'],root/'realism-fusion.jpg',width=600,columns=2)
    if localization_font:
        record = next(r for r in success if r['name'] == 'layers-poster-20')
        target = next(a for a in record['assets'] if a.get('text_recognition', {}).get('text') == 'GREEN STUDIO')
        canvas = compose(root, record, omit=[target['z_index']])
        box = target['text_recognition']['lines'][0]['bounding_box']['absolute']
        l,t,r,b = box
        text = '新绿工作室'
        draw = ImageDraw.Draw(canvas)
        font_size = b-t
        while font_size > 1:
            font = ImageFont.truetype(str(localization_font), font_size)
            ink = draw.textbbox((0,0),text,font=font)
            if ink[2]-ink[0] <= r-l and ink[3]-ink[1] <= b-t:
                break
            font_size -= 1
        color = target['text_recognition']['lines'][0]['runs'][0]['style']['foreground_color']
        draw.text((l-ink[0],t-ink[1]),text,font=font,fill=color)
        canvas.save(root/'localized-title.png')
        reference = np.asarray(compose(root,record).convert('RGB'),dtype=np.float32)
        localized = np.asarray(canvas.convert('RGB'),dtype=np.float32)
        preserve = np.ones(reference.shape[:2],dtype=bool)
        ll,tt,rr,bb=target['bounding_box']['absolute']
        preserve[tt:bb,ll:rr]=False
        summary['localization']={'protected_vs_recomposed':difference(reference,localized,preserve),'original_text' :'GREEN STUDIO','replacement':text,
            'omitted_z_index':target['z_index'],'base_coordinate_bbox':box,
            'font_substitution':localization_font.name,'font_size_fitted':font_size,
            'api_calls':0,'result':'localized-title.png'}
    (root/'analysis.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('chains','layers')},ensure_ascii=False,indent=2))
    for name,chain in summary['chains'].items():
        if chain['rounds']:
            last=chain['rounds'][-1]
            print(name,'rounds',len(chain['rounds']),'last vs original',last['original'])
    for rec in summary['layers']: print(rec['name'],rec['output_count'],rec['recomposition'])

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out_dir',type=Path)
    parser.add_argument('--localization-font',type=Path,help='Explicit available font for optional local title replacement demo.')
    args=parser.parse_args()
    main(args.out_dir.resolve(),args.localization_font)
