---
name: seedance-video-gen
description: >
  使用火山方舟 Seedance 2.5 系列生成视频、编辑或延长视频、优化提示词。适用于文生视频、首帧/首尾帧、多模态参考、30 秒视频和 Draft 样片。默认 Seedance 2.5 标准版；仅用户明确要求 flash 时使用 Seedance 2.5 flash。
---

# Seedance Video

把文本、图片、视频、音频参考变成视频素材。只支持 **Seedance 2.5 标准版与 flash**，使用同一套异步任务 API。默认标准版；用户明确说 flash 才选 flash。即使用户说「低成本」「快速预览」「批量」，也保持标准版，可通过缩短时长、降低分辨率控制成本。

## 模型选择与能力

| 模型 | Model ID | 输出分辨率 | 图 / 视频 / 音频上限 | Draft |
|---|---|---|---|---|
| **标准版（默认）** | `doubao-seedance-2-5-260628` | 480p / 720p / 1080p / 4k | 30 / 10 / 10 | 480p 样片 → 同模型 1080p / 4k |
| **flash（明确指定）** | `doubao-seedance-2-5-flash-261115` | 480p / 720p | 10 / 5 / 5 | 不支持 |

两者都支持 4–30 秒 / `-1` 智能时长、仅音频参考、编辑、延长、MP4/MOV、联网搜索（仅纯文本）。标准版支持 4K，flash 最高 720p。flash 的「速度约翻倍、成本约降低 34%」是发布介绍，实际耗时和费用以任务结果与实时价格为准，不能套用旧模型测速数据。

用户指定 flash 又要 1080p、4K 或 Draft：说明能力冲突，确认要调整哪项；不要静默换模型或降规格。完整能力和参数锁定见 [references/seedance-2.5.md](references/seedance-2.5.md)。

## 前置条件与边界

- `uv` 可用；脚本用 PEP 723 声明依赖，`uv run` 自动安装。
- `ARK_API_KEY` 环境变量或当前工作目录的 `.env`；可选 `ARK_BASE_URL`，默认 `https://ark.cn-beijing.volces.com/api/v3`。纯本地 `--dry-run` 不需要密钥。
- 图片和音频可用本地文件（自动转 data URL）、公网 URL 或 `asset://`；**视频仅公网 URL 或 `asset://`，不支持本地文件/base64**。
- 不直接上传含真人人脸的图/视频；预置虚拟人像、已授权素材、平台允许的同账号信任产物按官方规则使用。
- 本 skill 产出独立视频素材；视频搜索、后期剪辑、发布和超过 30 秒的分镜编排由上层任务负责。
- Files API 的 `file-...` 不是 `asset://` 素材 ID，视频生成没有文档化的 `file_id`/`file://` 输入。上传文件不代表可直接用于 Seedance。见 [references/files-api.md](references/files-api.md)。

## 快速使用

命令中的 `scripts/` 相对于本技能目录；从其他目录运行时替换为技能内脚本的绝对路径。

```bash
# 默认标准版；CLI 默认 5s / 16:9 / 720p / 有声 / 无水印
uv run scripts/generate_seedance_video.py \
  --prompt '黄昏海岸，一只橘猫坐在木栈道上，微风吹动毛发，镜头缓慢推进。无 bgm，只保留海浪声，不要字幕。'

# 仅在明确要求 flash 时显式选择；flash 最高 720p
uv run scripts/generate_seedance_video.py \
  --model doubao-seedance-2-5-flash-261115 \
  --prompt '红纸船沿林间溪流漂过，低机位跟拍，阳光在水面闪动。' \
  --duration 8 --resolution 720p

# 标准版 4K 终稿（10-bit HEVC）
uv run scripts/generate_seedance_video.py \
  --prompt '城市雨夜，霓虹倒映在路面，低机位缓慢前推。' \
  --duration 5 --ratio 9:16 --resolution 4k

# 首帧（两款模型均必须 adaptive；先把输入图裁成目标画幅）
uv run scripts/generate_seedance_video.py \
  --prompt '人物自然转身看向镜头，轻声说：“你好，好久不见。”不要字幕。' \
  --first-frame assets/start.png --duration 8 --ratio adaptive

# 首尾帧；不能与 reference_* 混用
uv run scripts/generate_seedance_video.py \
  --prompt '包装盒从闭合状态缓慢打开，产品从盒内显露。' \
  --first-frame assets/start.png --last-frame assets/end.png \
  --duration 5 --ratio adaptive

# 仅音频参考，两款模型均允许；输出音轨会重做，并非原样贴参考
uv run scripts/generate_seedance_video.py \
  --prompt '画面跟随音频1的节拍与情绪：黄昏海岸，镜头缓慢推进。不要字幕。' \
  --reference-audio assets/music.wav --duration 8

# 编辑：锁画幅与源视频时长；可用时间戳指定修改范围
uv run scripts/generate_seedance_video.py \
  --prompt '编辑视频1：仅将 0-2 秒的晴天改为雨夜，其余画面与音频保持不变。' \
  --reference-video https://example.com/src.mov \
  --omni-reference-task-type edit --ratio adaptive --duration -1 --output-format mov

# 延长：duration 是成片总时长（源5s，再续7s → 12）
uv run scripts/generate_seedance_video.py \
  --prompt '向后延长视频1。紧接视频1结尾：窗户打开，镜头推进室内。' \
  --reference-video https://example.com/src.mov \
  --omni-reference-task-type extend --ratio adaptive --duration 12 --output-format mov

# 标准版 Draft：480p 候选；flash 不支持
uv run scripts/generate_seedance_video.py --draft \
  --prompt '红纸船顺着溪流漂过，低机位跟拍。' --duration 4

# 看过并选定成功 Draft 后，凭 task ID 生成同模型 4K；省略 resolution 默认 1080p
uv run scripts/generate_seedance_video.py promote-draft --task-id cgt-xxx --resolution 4k
```

### 批量独立镜头

准备 JSON 数组，每项必填 `prompt`，可覆盖 `model`、`duration`、`ratio`、`resolution`、`draft`、`generate_audio`、`output_format`、`omni_reference_task_type` 及素材字段。素材字段可为字符串或数组；首帧最多一张，尾帧最多一张且必须有首帧。默认整批使用标准版；明确要求 flash 才传其 ID。

```json
[
  {"prompt": "产品正面45度特写，镜头缓慢推进。", "duration": 5, "ratio": "1:1"},
  {"prompt": "产品侧面轮廓，侧光勾勒边缘。", "duration": 5, "ratio": "1:1"}
]
```

```bash
uv run scripts/generate_seedance_video.py batch-submit \
  --shots-file /tmp/shots.json --wait --output-dir output/product-shots

# 标准版多个候选先做 Draft；逐个选择 task ID 升版
uv run scripts/generate_seedance_video.py batch-submit \
  --shots-file /tmp/shots.json --draft --wait
```

### 任务管理与本地检查

```bash
uv run scripts/generate_seedance_video.py create --prompt '黄昏海岸，海浪轻拍礁石。' --duration 5
uv run scripts/generate_seedance_video.py poll --task-id cgt-xxx
uv run scripts/generate_seedance_video.py list-tasks --status succeeded --page-size 20
uv run scripts/generate_seedance_video.py list-tasks --task-ids cgt-xxx cgt-yyy
uv run scripts/generate_seedance_video.py download --video-url https://example.com/video.mp4
uv run scripts/generate_seedance_video.py cancel-task --task-id cgt-xxx

# 仅纯文本可开启；模型自行决定是否调用搜索
uv run scripts/generate_seedance_video.py create --enable-web-search \
  --prompt '搜索近期航天进展，生成8秒科普视频。' --duration 8

# 验证请求 JSON，不调用 API、不需要 ARK_API_KEY
uv run scripts/generate_seedance_video.py create --dry-run \
  --model doubao-seedance-2-5-flash-261115 --prompt '纸船漂过溪流。' --duration 30
```

`cancel-task` 对 queued 取消排队；对 succeeded/failed/cancelled/expired 删除记录；running 不支持。具体状态、留存期与查询限制见 [references/api-reference.md](references/api-reference.md)。

## 提示词与迭代

官方 2.5 系列指南同时适用于标准版与 flash；**切换 flash 无需换提示词语法**。先确定任务类型，再让素材、prompt 意图、参数保持一致。

1. 单动作 4–5 秒：主体＋动作＋场景＋镜头＋声音即可。
2. 多镜头/长叙事：素材编号与用途 → 一句话概述 → 连续整数秒时间轴或镜头序号 → 全片约束。每段留够动作与对白时长，不为凑满 30 秒堆动作。
3. 多素材：按各类型传入顺序写「图片1锁角色外观，视频1参考运镜，音频1参考音色」，不用图片里的文字代替绑定。
4. 编辑：写「将视频1的 A 改为 B」，限定时间段、对象与需保留的内容。延长：写前/后方向与紧接边界的具体事件。
5. 对白用引号并明确说话人；「无 bgm，只保留环境音」「不要额外字幕」可直接写入 prompt。括号标记是组织习惯，不是 API 控制符；无声视频用 `--no-generate-audio`。
6. 看完整成片后针对一个问题修改。标准版若最终要 1080p / 4K 且需要挑多个方向，可先 Draft；flash 预览是普通 480p/720p 生成，没有 task ID 升版路径。

详细写法见 [references/prompt-guide.md](references/prompt-guide.md)，场景示例见 [references/scene-cookbook.md](references/scene-cookbook.md)，素材传输和稳定性建议见 [references/multimodal-reference.md](references/multimodal-reference.md)。

## Draft 与交付

标准版 Draft 生成 480p，选中后 `promote-draft` 生成 1080p 或 4K；两步独立计费，升版继承原 prompt、素材、时长等，不能同时修改。需要改输入时创建新 Draft。用户要求挑片时先展示样片供选择；已授权自动挑选时可自行比较再升版。详见 [references/draft-mode.md](references/draft-mode.md)。

**留存期**：2026-10-28 10:00（UTC+8）及之后创建的 Draft ID 有效 14 天，更早的为 7 天；其他任务 ID 为 7 天。产物 URL 有效 24 小时、最多下载 100 次，成功后及时下载。

交付时报告实际模型、分辨率、时长、task ID、视频路径，以及普通生成/Draft/升版。失败时解释实际错误并给可执行修正。普通生成脚本写入 `manifest.json` 和 `prompt.md`；升版脚本不自动复制原 prompt，调用者需从来源目录手动保留原文件或记录其路径。

```text
output/seedance/YYYY-MM-DD-<slug>/
├── video.mp4               # 或 video.mov
├── manifest.json           # task_id、模型、实际参数、usage、输出路径
├── prompt.md
└── last-frame.jpg          # --return-last-frame；JPEG
```

## 参数与限制速查

| 参数 | CLI 默认 / 约束 |
|---|---|
| `--model` | 标准版；仅明确要求 flash 时使用其完整 ID |
| `--duration` | `5`；支持整数 4–30 或 `-1`。编辑必须 -1，延长为成片总时长 |
| `--ratio` | `16:9`；支持 16:9/4:3/1:1/3:4/9:16/21:9/adaptive；首帧、编辑、延长必须 adaptive |
| `--resolution` | 普通生成 720p；Draft 480p；标准版支持 4k；flash 不支持 1080p / 4k |
| `--prompt` / `--prompt-file` | 文本 / UTF-8 文件；中文建议 ≤500 字、英文 ≤1000 词 |
| `--first-frame` / `--last-frame` | 本地文件或 URL/asset；首尾帧模式与 reference_* 互斥 |
| `--reference-image/video/audio` | 可重复；按所选模型分别校验上限 |
| `--output-format` | API 默认 mp4；可指定 mov，两模型均支持 |
| `--omni-reference-task-type` | auto/reference/edit/extend；显式指定可提前校验，仍需匹配 prompt |
| `--draft` / `promote-draft` | 仅标准版；480p → 同模型 1080p / 4k；升版默认 1080p，可显式 `--resolution 4k` |
| `--generate-audio` / `--no-generate-audio` | 默认 true，生成双声道音频 |
| `--watermark` / `--return-last-frame` | 默认 false；尾帧 JPEG |
| `--priority` | 0–9，同 Endpoint 内优先级 |
| `--enable-web-search` | 仅纯文本，不保证实际搜索 |
| `--poll-interval` / `--max-wait` | 20 秒 / 1800 秒；本地等待超时不会取消服务端任务 |
| `--output-dir` | `SEEDANCE_OUTPUT_DIR` 或 `output/seedance` |
| `--dry-run` | generate/create/promote-draft 的本地请求检查；升版 dry-run 不查询来源 ID |

输入媒体体积、格式与时长，以及 API 专有字段见 [references/key-constraints.md](references/key-constraints.md) 和 [references/api-reference.md](references/api-reference.md)。速率与并发以当前账号配额为准，不用旧模型压测结果推断 flash 配额。

4K 输出采用 10-bit HEVC；16:9 为 3840×2160，9:16 为 2160×3840。官方教程列出标准版 4K 企业/个人均为 15 RPM、最大并发 1；实际限流与价格以账号配置和[官方价格](https://console.volcengine.com/ark/region:cn-beijing/docs/model-pricing)为准。
