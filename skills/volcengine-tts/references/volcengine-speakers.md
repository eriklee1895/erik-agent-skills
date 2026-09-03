# Volcengine TTS Voice Guide (seed-tts-2.0)

This file is **TTS-specific selection guidance**, not the full catalog.

- Full catalog (444 voices, same ListSpeakers snapshot as `seed-audio-gen`): query with `--list-speakers`
- Curated Top 5 per scene + trial links: `references/speakers.md`
- Do **not** read `references/speakers.json` into context (~220KB)

```bash
uv run scripts/volcengine-tts.py --list-speakers
uv run scripts/volcengine-tts.py --list-speakers --filter type=bigtts --sort heat
uv run scripts/volcengine-tts.py --list-speakers --filter scene=教学场景
uv run scripts/volcengine-tts.py --list-speakers --filter lang=ja --sort heat
```

Last catalog snapshot: 2026-08-27 (244 bigtts + 200 ICL).
Source: ListSpeakers OpenAPI (AK/SK); public voice page https://www.volcengine.com/docs/6561/1257544

Official seed-tts-2.0 HTTP synthesis (`X-Api-Resource-Id: seed-tts-2.0`) is documented to accept 豆包语音合成模型2.0 voices. Prefer `_bigtts` / `type=bigtts` for this skill. Catalog `_tob` / ICL voices may need `--model seed-tts-2.0-standard`; user-cloned `S_xxx` speakers belong to `seed-icl-2.0`, not this skill.

---

## Voice Recommendation by Scenario

### AI Video Voiceover / 旁白配音

| Use Case | Recommended Speaker | ID |
|----------|-------------------|-----|
| 技术解说 / Tech explainer | 云舟 2.0 | `zh_male_m191_uranus_bigtts` |
| 故事旁白 / Story narration | 温柔妈妈 2.0 | `zh_female_wenroumama_uranus_bigtts` |
| 悬疑/侦探 / Suspense | 悬疑解说 2.0 | `zh_male_xuanyijieshuo_uranus_bigtts` |
| 广告营销 / Commercial | 广告解说 2.0 | `zh_male_guanggaojieshuo_uranus_bigtts` |
| 纪录片 / Documentary | 磁性解说男声 2.0 | `zh_male_cixingjieshuonan_uranus_bigtts` |
| 温柔文艺 / Literary | Vivi 2.0 | `zh_female_vv_uranus_bigtts` |
| 情感鸡汤 / Inspirational | 鸡汤女 2.0 | `zh_female_jitangnv_uranus_bigtts` |

### Podcast / 播客

| Use Case | Recommended Speaker | ID |
|----------|-------------------|-----|
| 深夜播客 / Late-night | 深夜播客 2.0 | `zh_male_shenyeboke_uranus_bigtts` |
| 文化对谈 / Culture talk | 儒雅逸辰 2.0 | `zh_male_ruyayichen_uranus_bigtts` |
| 女性视角 / Female POV | 知性女声 2.0 | `zh_female_zhixingnv_uranus_bigtts` |

### Educational / 教育

| Use Case | Recommended Speaker | ID |
|----------|-------------------|-----|
| 英语教学 / English teaching | Tina老师 2.0 | `zh_female_yingyujiaoxue_uranus_bigtts` |
| 少儿内容 / Kids content | 少儿故事 2.0 | `zh_female_shaoergushi_uranus_bigtts` |

### Character Voices / 角色配音

| Use Case | Recommended Speaker | ID |
|----------|-------------------|-----|
| 孙悟空 / Monkey King | 猴哥 2.0 | `zh_male_sunwukong_uranus_bigtts` |
| 猪八戒 | 猪八戒 2.0 | `zh_male_zhubajie_uranus_bigtts` |
| 唐僧 | 唐僧 2.0 | `zh_male_tangseng_uranus_bigtts` |
| 儿童角色 / Child | 佩奇猪 2.0 | `zh_female_peiqi_uranus_bigtts` |
| 古装角色 / Period drama | 古风少御 2.0 | `zh_female_gufengshaoyu_uranus_bigtts` |
| 霸道总裁 | 傲娇霸总 2.0 | `zh_male_aojiaobazong_uranus_bigtts` |

### English Voiceover

| Use Case | Recommended Speaker | ID |
|----------|-------------------|-----|
| 通用美式女声 / General US female | Dacey | `en_female_dacey_uranus_bigtts` |
| 通用美式男声 / General US male | Tim | `en_male_tim_uranus_bigtts` |
| 替代美式女声 / Alternative US female | Stokie | `en_female_stokie_uranus_bigtts` |
| ICL English male (catalog) | Michael 2.0 | `ICL_uranus_en_male_michael_tob` |

For other languages, run `--list-speakers --filter lang=<code> --sort heat` (`ja`, `ko`, `es-mx`, `id`, `pt-br`, …).

---

## Voice Capabilities

All official seed-tts-2.0 `_bigtts` voices support:

- **情感变化 (Emotion variation)**: Voices can express different emotions through natural-language voice instructions.
- **指令遵循 (Instruction following)**: Voices respond to `context_texts` like "用特别痛心的语气说话" out of the box — no special model flag required for public (non-cloned) voices.
- **ASMR**: Whispering and breathy styles available.
- **方言 (Dialects)**: Selected voices support Sichuan, Shaanxi, Dongbei and other dialects (check `--list-speakers` or the voice catalog).

### The `model` Parameter

For the public seed-tts-2.0 voice catalog (speaker IDs ending in `_bigtts`), you generally **do not need to set `model`** — the server picks the correct variant automatically and `context_texts` voice instructions work by default.

The `model` field is mainly relevant when using **cloned (ICL, 声音复刻) or `_tob` catalog voices**:

| Model | Notes |
|-------|-------|
| `seed-tts-2.0-standard` | Default for cloned / ICL voices; lower latency; voice-instruction QA / CoT tags are filtered out if passed |

Public `_bigtts` voices don't need this. If you see older docs referencing `seed-tts-2.0-expressive`, that variant no longer appears in the current (2026-06) API reference — emotion/instructions are built into the default model.

Official HTTP synthesis docs (`X-Api-Resource-Id`) also distinguish:

| Resource ID | Speakers it is documented to accept |
|-------------|-------------------------------------|
| `seed-tts-2.0` | 豆包语音合成模型2.0 (`*_uranus_bigtts`) — this skill's default |
| `seed-icl-2.0` | 声音复刻 2.0 (`S_xxx` user clones) — separate skill |

If synthesis returns `55000000: resource ID is mismatched with speaker`, the speaker is not valid for `seed-tts-2.0`. Try `--model seed-tts-2.0-standard` for `_tob` ICL catalog voices, or switch to the ICL skill for `S_xxx` clones.

---

## Using Voice Instructions (context_texts)

Pass a natural-language instruction via `--context` (no `--model` needed for `_bigtts`):

```
--context "用特别痛心的语气说话"
--context "像深夜电台主持人一样温柔低沉地读"
--context "像新闻联播主播一样字正腔圆地播报"
--context "Read like an excited startup founder giving a keynote"
```

The `context_texts` field is **not billed** — only the main `text` content counts toward usage.
