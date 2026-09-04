---
name: seedance-video-gen
description: |
  火山引擎 Seedance 2.5 / 2.0 视频生成。用户说”生成视频””Seedance 2.5””即梦””图生视频””文生视频””30秒视频””首尾帧””多模态参考””优化 Seedance 提示词”等时使用；同一套异步 API。默认 2.5；只要 4k 且无 2.5 独有需求则 2.0 standard；4k 与 2.5 能力冲突则先问；便宜预览用 2.0-fast/mini。
---

# Seedance Video

用火山引擎 Seedance 把文字、图片或多模态参考生成视频。默认 **Seedance 2.5**（`doubao-seedance-2-5-260628`，最长 30s，无 4k、无 fast/mini）。用户明确要 2.0、只要 4k、或便宜预览时切 2.0；4k 与 2.5 独有能力冲突则停下来问。

## 何时使用

- 用户给了一段脚本/描述，要生成视频。
- 用户给了一张图，要做成动态短视频（首帧或首尾帧）。
- 用户想基于文章、产品说明或已有图片生成多个视频镜头。
- 用户想优化 Seedance 提示词、运镜或光影描述。

## 不适用范围

- 不处理视频搜索、版权判断、剪辑后期。
- 不直接发布到任何平台。
- 不支持输入含真实人脸的素材（Seedance 限制；预置虚拟人像 `asset://` 与已授权真人素材除外）。
- 本地图片和本地音频会自动转成 base64 data URL 上传；**本地视频不支持 base64**，必须先传到可公开访问的 URL（TOS / S3 / 公网 bucket），或使用 `asset://` 素材 ID。

## 前置条件

- `uv` 可用；依赖由脚本 PEP 723 inline metadata 自声明，`uv run` 自动安装。
- 环境变量 `ARK_API_KEY` 已设置；或当前工作目录有 `.env` 文件包含 `ARK_API_KEY=`。
- 可选：`ARK_BASE_URL` 用于自定义网关（默认火山方舟 `https://ark.cn-beijing.volces.com/api/v3`）。

## 快速用法

> **默认模型**：省略 `--model` = Seedance 2.5 `doubao-seedance-2-5-260628`。2.5 无 fast/mini、无 4k。
> **何时切 2.0**：用户明确要 2.0 / 即梦 2.0（没说 fast/mini）→ standard；只要 4k 且无 2.5 独有需求 → 直接 2.0 standard + 4k；4k 且要 2.5 能力 → 先问。便宜预览/批量 → fast/mini。决策树见下方。
> **时长**：2.5 为 4–30s / `-1`；2.0 为 4–15s / `-1`。脚本 CLI 默认仍是 5s（控成本）；官方 2.5 API 默认是 `-1`。
> **2.5 首帧/首尾帧**：`--ratio` **必须** `adaptive`（画幅锁到首帧图）。编辑：`--ratio adaptive --duration -1`；延长：`--ratio adaptive`。

```bash
# 文生视频（默认 2.5，终稿 1080p；2.5 的 1080p 是 10-bit HEVC）
uv run scripts/generate_seedance_video.py \
  --prompt "一只橘猫在阳光下缓慢眨眼，微风吹动毛发，镜头轻微推进" \
  --duration 5 --ratio 1:1 --resolution 1080p

# 文生视频（2.0 fast 快速预览，~40% 成本，最高 720p）
uv run scripts/generate_seedance_video.py \
  --model doubao-seedance-2-0-fast-260128 \
  --prompt "一只橘猫在阳光下缓慢眨眼，微风吹动毛发，镜头轻微推进" \
  --duration 5 --ratio 1:1 --resolution 720p

# 2.5 首帧图生视频（ratio 必须 adaptive）
uv run scripts/generate_seedance_video.py \
  --prompt "让人物自然转身看向镜头，保持电影级光影，{你好，好久不见}" \
  --first-frame assets/start-frame.png \
  --duration 8 --ratio adaptive

# 2.5 首尾帧（ratio 必须 adaptive）
uv run scripts/generate_seedance_video.py \
  --prompt "顺滑的产品外观转场，不出现人物" \
  --first-frame assets/start.png \
  --last-frame assets/end.png \
  --duration 4 --ratio adaptive

# 显式 2.0 standard（例如要 4k）
uv run scripts/generate_seedance_video.py \
  --model doubao-seedance-2-0-260128 \
  --prompt "城市夜景航拍，镜头缓慢前推" \
  --duration 5 --ratio 16:9 --resolution 4k

# 只创建任务，拿到 task_id（多分镜叙事用长时长）
uv run scripts/generate_seedance_video.py create \
  --prompt "霓虹雨夜街道，摩托车飞驰而过，镜头跟拍穿过雨幕，<引擎轰鸣声>" \
  --duration 10

# 查询已有任务
uv run scripts/generate_seedance_video.py poll \
  --task-id cgt-xxx

# 下载已有视频 URL
uv run scripts/generate_seedance_video.py download \
  --video-url https://example.com/video.mp4

# 列出最近 7 天的任务（按状态筛选）
uv run scripts/generate_seedance_video.py list-tasks \
  --status succeeded --page-size 20

# 按模型 + 多个 task_id 精确搜索
uv run scripts/generate_seedance_video.py list-tasks \
  --model doubao-seedance-2-5-260628 \
  --task-ids cgt-20260606xxxx-xxxx cgt-20260606yyyy-yyyy

# 2.5 编辑视频（ratio+duration 锁定；mov 便于后期）
uv run scripts/generate_seedance_video.py create \
  --prompt "编辑视频1：把晴天改成雨夜，保持运镜不变" \
  --reference-video https://example.com/src.mp4 \
  --ratio adaptive --duration -1 \
  --omni-reference-task-type edit --output-format mov

# 2.5 仅音频参考（Ark live 已通；音频须有语义，不要纯正弦）
uv run scripts/generate_seedance_video.py create \
  --prompt "画面跟随音频1的节拍与情绪：黄昏海岸镜头缓慢前推，<海浪>，不要字幕。" \
  --reference-audio assets/score.wav \
  --duration 8 --ratio 16:9 --resolution 1080p

# 2.5 延长。--duration 是成片总时长（源 5s 再续 7s → 12），不是「再延长 N 秒」
uv run scripts/generate_seedance_video.py create \
  --prompt "向后延长@视频1。紧接视频1结尾：窗户打开，镜头推进室内。不要字幕。" \
  --reference-video https://example.com/src.mov \
  --ratio adaptive --duration 12 \
  --omni-reference-task-type extend --output-format mov

# 取消/删除任务（按当前状态不同行为不同，见 references/api-reference.md）
uv run scripts/generate_seedance_video.py cancel-task --task-id cgt-20260606xxxx-xxxx
```

### 批量提交（并行原子 shots）

适合一次性并行提交多个独立短视频片段（2.5 最长 30s，2.0 最长 15s），每个 task 独立生成、独立 task_id。**不是**长视频分镜编排（那是单独的 longform skill 干的事）。

典型场景：
- A/B 测试同一 prompt 的多个变体，挑最好的
- 产品多角度展示（5 个角度一次提交）
- 文章多段落配图（每段独立视频，无剧情关联）
- 批量生成素材备选库

读 JSON 文件，每个 shot 一个 object，可独立覆盖任意参数。

```bash
# 准备 shots.json
cat > /tmp/shots.json << 'EOF'
[
  {"prompt": "产品正面 45 度角特写", "duration": 4, "ratio": "1:1"},
  {"prompt": "产品侧面轮廓", "duration": 4, "ratio": "1:1"},
  {"prompt": "产品俯视角度", "duration": 4, "ratio": "1:1"}
]
EOF

# 一次性并行提交（3 个独立 task）
uv run scripts/generate_seedance_video.py batch-submit \
  --shots-file /tmp/shots.json \
  --model doubao-seedance-2-0-fast-260128 \
  --resolution 480p

# 加 --wait：等所有完成 + 自动下载到指定目录（可选）
uv run scripts/generate_seedance_video.py batch-submit \
  --shots-file /tmp/shots.json --wait --output-dir output/product-shots
```

### 联网搜索（仅纯文本输入，引用当前事件/最新数据）

```bash
uv run scripts/generate_seedance_video.py create --enable-web-search \
  --prompt "搜索 2026 年 AI 视频生成最新进展，做 8s 总结短视频" \
  --duration 8 --ratio 9:16
```

> web_search 由模型自主决定调用次数（可能 0 次），会增加生成延迟；只在需要「模型权重外信息」时开启。详细约束见 `references/key-constraints.md`。

## 工作流程

Seedance 视频生成是**强迭代**工作流，不是一次出片。下面是决策启发式，不是固定流水线——根据任务复杂度、用户阶段（探索 / 微调 / 出片）和反馈取舍。

### 判断任务形态

先搞清楚用户处于哪个阶段，这决定你后面投入多少优化：

| 阶段 | 特征 | 策略 |
|---|---|---|
| 探索/脑暴 | 用户自己也不清楚要什么、想看可能性 | 2.0-fast + 480p/720p + 4-5s，一次 2-3 个变体；或 2.5 短时长看质量上限 |
| 调参/迭代 | 已有初版，要修具体问题（换脸/字幕/运镜） | 保留原 prompt，小步修改；预览用 2.0-fast，质量问题改用 2.5 |
| 出片/交付 | 要最终成品 | **默认 2.5** + 目标分辨率（2.5 最高 1080p HEVC；只要 4k 且无 2.5 独有需求 → 2.0 standard）|
| 批量素材 | 多段落独立配图/产品多角度 | batch-submit + 2.0-fast/mini |

### 模型 / 分辨率 / 时长选择启发式

不要盲目用默认值。按场景挑。

**模型选择（用户说了什么 → 立刻做什么）。** 能唯一确定就别问；不要每次提到 4k 都问。脚本已拦截 `2.5 + 4k`。

| 用户说了什么 | 立刻做什么 |
|---|---|
| 没指定模型 | **2.5** `doubao-seedance-2-5-260628` |
| 明确要 2.0 / seedance 2.0 / 即梦 2.0，没说 fast/mini | **2.0 standard** `doubao-seedance-2-0-260128`。便宜预览/批量才 fast/mini |
| 明确要 4k，且没有 2.5 独有需求 | **直接 2.0 standard + `--resolution 4k`**，并告知一句：`4k 只能 Seedance 2.0 standard，2.5 最高 1080p。` |
| 要 4k **且** 要 2.5 独有能力 | **停下来让用户选**：A) 4k + 2.0（最长 15s，无那些 2.5 能力）或 B) 留在 2.5 用 1080p。不要擅自猜 |

**2.5 独有需求**（命中才算和 4k 冲突）：30s、整数秒时间戳硬切、仅音频参考、omni 编辑/延长、mov 后期。

2.5 **没有** fast/mini。4s 480p 时 2.0-fast 与 2.5 的 completion_tokens 几乎一样（~38800）；fast 便宜在 **2.0 更低的单价**，不是 token 腰斩。

- **分辨率**：预览 → 480p；社媒/草稿 → 720p（CLI 默认）；2.5 终稿 → 1080p（10-bit HEVC）；4k → 仅 2.0 standard（10-bit HEVC，并发 1）
- **时长**：单一动作 → 4-5s；对白/多镜头 → 8-12s；2.0 复杂叙事 → 12-15s 或拆 task；2.5 完整故事可一次 15-30s，prompt 用整数秒时间戳。480p 文生 token ≈ `38830 × (duration/4)`
- **ratio**：竖屏 9:16、横屏 16:9、方 1:1、宽银幕 21:9。**2.5 首帧/编辑/延长必须 `adaptive`**。CLI 文生默认仍是 `16:9`（官方 2.5 API 默认 `adaptive`）
- **音频**：对话/旁白/广告 → 默认生成；后期自配 → `--no-generate-audio`。仅音频参考：**仅 2.5 允许**（Ark live 已通）；参考须是有语义的 wav/mp3
- **2.5 新参数**：后期调色/编辑延长建议 `--output-format mov`；明确编辑/延长时加 `--omni-reference-task-type edit|extend` 把校验前置。延长的 `--duration` 是成片总时长

### 何时必须用 2.5（按用户意图锁模型，不要先降到 fast）

命中下表任一行就走默认 2.5。这些不是「2.5 更好看」，是 2.0 **没有这条路或会 400**。

| 用户说了什么 | 立刻用的参数 | 实测注意 |
|---|---|---|
| 「一条 16–30 秒」「不要拆成多段再拼」 | `--duration 16–30`，prompt 连续整数秒 | 16s 480p live 成片 16.06s，token 154,120 ≈ 4s 的 4 倍 |
| 「第 N 秒切镜 / Hard cut / 0-4s 再 4-8s」 | 分段 prompt：`GLOBAL STYLE` + `Shot N: 0-xs … Hard cut.` | live：4s 硬切会换镜头；「航拍拉升」等运镜动词只部分兑现，景别边界比动词可靠 |
| 「只有配乐/旁白，没有图」 | `--reference-audio file.wav`（不要配图） | Ark **允许仅音频**（create+succeeded）。纯正弦几乎不驱动画面；`generate_audio=true` 会重做音轨，不是原样贴参考 |
| 「用这张图当第一帧」 | `--first-frame` + **`--ratio adaptive`** | 非 adaptive → HTTP 400 `TaskTypeConstraint`。adaptive 画幅锁首帧（响应 ratio 如 `427:240`） |
| 「改这段视频：删人/换天气/替换物体」 | `--omni-reference-task-type edit --ratio adaptive --duration -1` | duration `-1` 成片时长≈源片。live 任务通；「保持运镜不变」不一定兑现，删路人可能长出新主角——prompt 写死「不要新增人物」 |
| 「把这段往后/往前续」 | `--omni-reference-task-type extend --ratio adaptive`，`--duration`=**成片总时长** | 源 5s 再续 7s → `--duration 12`。prompt 必须写「紧接@视频1结尾：具体动作」。只写「延续同一场景」可能整段换景 |
| 「要 mov 给后期调色」 | `--output-format mov` | live 4s 480p URL `.mov`，token 与 mp4 相同 |
| 「参考图超过 9 / 视频超过 3」 | 默认 2.5；每元素仍各 1 份 | 上限 30/10/10 共 50，不要堆满 |
| 白模 / 宫格 / 多关键帧 / 跨镜锁身份 | prompt-guide **§3**（白模/宫格/关键帧）；跨镜锁 **§2** | 宫格 ≤15；关键帧第一句见 §3.1 |

**不要用 2.5**：只要便宜预览/批量短片 → `--model doubao-seedance-2-0-fast-260128` 或 mini。要 4k 见上方决策树（无 2.5 独有需求才切 2.0 standard；脚本会拦截 2.5+4k）。2.5 无 fast。

### 2.5 复杂镜头怎么写（吃满能力）

简单 4–5s 仍用一句话。**多切镜 / 30s / 要跨镜头不换脸** 时用分段结构（一项不写就会在对应维度翻车，不是「写得越长越好」）：

```
GLOBAL STYLE：类型、色调、片种、画幅、禁止出现什么
SCENE：一句话发生了什么
CHARACTERS / LOCATION：人或空间；有参考图就点名「图片N 是谁」
FIRST FRAME AND BLOCKING：开场谁在哪、朝哪
Shot 1: … Hard cut.
Shot 2: 0-4s … 4-10s …
OPTICS / LIGHTING / PHYSICS：焦段或机位、光从哪来、布料/烟/液体怎么动
AUDIO：环境音、音效、不要什么。默认「无 bgm、无额外字幕」，对白用 {}
```

复杂分段、named locks、角色表、时间戳规则见 [prompt-guide.md](references/prompt-guide.md) **§2**。白模/宫格/关键帧/仅音频见 **§3**。场景模板见 [scene-cookbook.md](references/scene-cookbook.md)。

30s 是上限不是目标；只有一个动作就 4–8s。10–15 次迭代仍烂：拆场景。一次只改一个变量。看完整成片再判。

### 写提示词：按 shot 复杂度伸缩

- **简单 shot**（4-5s 单一动作/产品/场景）：一句话点明主体+动作+风格即可
- **中等 shot**：主体 + 动作 + 场景 + 运镜 + 风格
- **复杂 shot**（多人/多镜头/30s 叙事/编辑延长）：prompt-guide §2 分段结构。**2.5 用连续整数秒**（`0-3s` / `[1s-4s]`）；2.0 只认镜头序号，不要写精确秒数（附录 A）
- 音频符号不变：`（）`音乐、`<>`音效、`{}`台词、`【】`字幕。2.5 负向控制见 prompt-guide §3.3
- 细节见 [prompt-guide.md](references/prompt-guide.md)（2.5-first；2.0 见附录 A）；参数差异见 [seedance-2.5.md](references/seedance-2.5.md)
- 参考素材绑定规则见 [references/multimodal-reference.md](references/multimodal-reference.md)

### 准备参考素材（可选）

Seedance skill 不负责生成或获取素材——它只消费调用方传入的素材。纯文生视频不需要任何素材，直接跑即可。

当调用方（用户或上层编排 skill）提供素材时：
- 用户直接给的图片/视频/音频 → 直接用，注意比例/分辨率/内容和格式要求
- 本地图片（png/jpg/jpeg/webp/gif/bmp/tiff/heic/heif）和本地 wav/mp3 音频 → 脚本自动转 base64，直接传路径
- 本地视频 → **不支持 base64**，必须先上传公网 URL 或录入 asset:// 素材库再传 URL
- 素材组合规则、绑定语法、编辑/延长模式见 [references/multimodal-reference.md](references/multimodal-reference.md)
- 尾帧、参考视频、参考音频只有在链式续写/动作对齐/音色对齐时才需要；简单 shot 不必凑

### 提交前校验（复杂任务建议）

简单 shot 直接跑；**多参考素材/首尾帧+视频+音频组合/批量 10+ 任务/4k** 这些费钱费时间的请求，先 `--dry-run` 看 payload 是否合理，再真正提交。

### 执行与等待

- 单个 task 墙钟（`created_at`→`updated_at`，2026-09-03 Ark）：2.0-fast 4s 480p ~75s；2.5 文生 4s 480p ~2–2.5 min；12s ~2.7 min；16s ~3 min；首帧 4s ~3.7 min；编辑 16s ~3.6 min。1080p 更久。详见 `references/seedance-2.5.md`
- **submit 任务（POST /tasks）2.0 实测不限流**（普通公司开发账号）：可 burst 提交。并发限制的是同时 `running` 数量。官方 2.5 与 2.0 非 4k 相同：企业 600 RPM / 10 concurrent，个人 180 / 3
- 4k task（仅 2.0 standard）严格串行（running 1，RPM 15）
- 轮询间隔默认 20s 就够，不要开得太频繁
- 需要只拿 task_id 稍后再查：用 `create` 子命令；需要同步等结果：用默认 `generate`

### 迭代是正常的

第一次生成结果不满意很正常。典型迭代模式：
1. 看视频：问题是人/动作/运镜/光影/字幕/音频中哪一个？
2. 对应修正 prompt 或换参考素材（一次只改一个维度）
3. 2.0-fast 快速验证（或短时长 2.5）
4. 通过后再用 2.5（或 2.0 standard 4k）+ 目标分辨率出终稿
- 常见问题的 prompt 层解法见 [references/prompt-guide.md](references/prompt-guide.md) 和 [references/key-constraints.md](references/key-constraints.md) 的翻车清单
- 同一 prompt 生成 2-3 次挑最好的，对复杂 shot 是划算的

### 交付

报告用户：输出目录、视频路径、task_id、是否终稿还是预览版。失败时把 `manifest.json` 的 error 字段转成可执行建议（"分辨率参数错了改用 720p"而不是"API 返回 400"）。

需要追溯/复盘/分享终稿时，把最终 prompt 写入输出目录的 `prompt.md`；一次性预览和失败的尝试不必留 artifact。

## 输出目录

```text
output/seedance/YYYY-MM-DD-<slug>/
├── video.mp4               # 或 video.mov（2.5 `--output-format mov`）
├── manifest.json           # task_id, model, params, video_url, usage, output paths
├── prompt.md               # 最终提示词
└── last-frame.jpg          # 仅当 --return-last-frame
```

## 重要约束

按模型分流。2.5 任务类型硬限制见 [references/seedance-2.5.md](references/seedance-2.5.md)。

- `duration`：2.5 = `4–30` 或 `-1`；2.0 = `4–15` 或 `-1`。CLI 默认 `5`。编辑必须 `-1`。**延长的 duration 是成片总时长**。
- `resolution`：`480p` / `720p` / `1080p` / `4k`；CLI 默认 `720p`。**2.5 最高 1080p（10-bit HEVC），无 4k**。2.0-fast/mini 最高 720p。**4k 仅 2.0 standard**。
- `ratio`：六档 + `adaptive`。CLI 文生默认 `16:9`。**2.5 首帧/首尾帧、编辑、延长必须 `adaptive`**（脚本会拦截）。
- 多模态上限：2.5 = 图 30 + 视 10 + 音 10（共 50）；2.0 = 图 9 + 视 3 + 音 3（脚本 total ≤ 12）。仍建议 4-5 个素材黄金配比。
- 仅音频参考：2.5 ✅（Ark live 已通，脚本不拦）；2.0 ❌（必须配图或视频）。参考须有语义的 wav/mp3。
- 首尾帧与 `reference_*` **互斥**（两代相同）。
- `--enable-web-search` 仅纯文本（两代相同）。
- 2.5 新字段：`output_format`=`mp4|mov`（mov 仅 2.5）；`omni_reference_task_type`=`auto|reference|edit|extend`（仅 2.5）。
- 本地图片/音频可 base64；**本地视频必须 URL 或 `asset://`**。真人人脸输入禁止（asset:// / 授权 / 信任产物除外）。

> 完整参数表、计费、状态机、错误码见 [references/api-reference.md](references/api-reference.md)。

## 参数速查

| 参数 | 说明 |
|---|---|
| `--prompt, -p` | 文本提示词 |
| `--prompt-file` | 提示词文件路径 |
| `--first-frame` | 首帧本地图片路径 |
| `--last-frame` | 尾帧本地图片路径 |
| `--reference-image` | 多模态参考图（可重复） |
| `--reference-video` | 多模态参考视频（可重复） |
| `--reference-audio` | 多模态参考音频（可重复） |
| `--model` | 默认 `doubao-seedance-2-5-260628`；2.0 三个 ID 仍可用 |
| `--duration` | 2.5: 4–30 / -1；2.0: 4–15 / -1；CLI 默认 5。编辑必须 -1；延长 = 成片总时长 |
| `--ratio` | 六档 + adaptive；2.5 首帧/编辑/延长必须 adaptive |
| `--resolution` | 480p/720p/1080p/4k；2.5 无 4k |
| `--output-format` | 2.5 only：`mp4`（默认不传）或 `mov` |
| `--omni-reference-task-type` | 2.5 only：`auto` / `reference` / `edit` / `extend` |
| `--generate-audio` / `--no-generate-audio` | 是否生成音频 |
| `--watermark` / `--no-watermark` | 是否加水印 |
| `--return-last-frame` | 返回尾帧图 |
| `--priority` | 任务优先级（`0-9`），数值越大越靠前（仅同 Endpoint 内 FIFO 排序） |
| `--enable-web-search` | 联网搜索工具；**仅纯文本输入**，与多模态互斥 |
| `--output-dir` | 输出根目录，默认 `output/seedance/`（可被 `SEEDANCE_OUTPUT_DIR` env var 或 `--output-dir` 覆盖） |
| `--poll-interval` | 轮询间隔，默认 20 秒 |
| `--max-wait` | 最大等待秒数，默认 1800 秒（30 分钟） |
| `--dry-run` | 只构建并打印请求，不调用 API |
| `--verbose` | 打印更多调试信息 |

> 完整 4 端点 + 完整请求/响应字段 + 完整分辨率像素表见 [references/api-reference.md](references/api-reference.md)。

## 参考文件

Agent 按需读取，不必全加载。简单任务（文生视频 4-5s、单镜头）直接跑即可，不必先读 reference；复杂任务、遇到错误、准备多模态素材、或要写精细 prompt 时再查。

| 文件 | 用途 | 何时读 |
|---|---|---|
| `references/seedance-2.5.md` | 2.5 vs 2.0 差异、任务类型锁定、新参数、prompt 增量、不兼容点 | 用 2.5 / 30s / 首帧 / 编辑延长 / mov 之前 |
| `references/key-constraints.md` | 能力边界、硬限制、翻车清单、并发、4k | 第一次用 / API 报错 / 4k 或多模态 |
| `references/multimodal-reference.md` | 多模态输入、asset://、编辑/延长 | 准备参考素材时 |
| `references/prompt-guide.md` | 2.5-first 提示词公式；2.0 见附录 A | 写 prompt / 迭代失败时 |
| `references/scene-cookbook.md` | 场景配方（默认 2.5 时间戳；2.0 见各节改写） | 需要模板时 |
| `references/api-reference.md` | 端点、字段、状态机、错误码、计费 | 调试 API 时 |

## 故障排查

| 现象 | 处理 |
|---|---|
| `ARK_API_KEY not found` | 检查环境变量或 `.env` 文件 |
| `400 InvalidParameter.TaskTypeConstraint` | 2.5 首帧/编辑/延长参数和任务类型不一致。首帧必须 `--ratio adaptive`；编辑还要 `--duration -1` |
| 脚本拒绝 `--resolution 4k` | 2.5 / 2.0-fast / mini 无 4k；4k 用 `--model doubao-seedance-2-0-260128` |
| 脚本拒绝 `--resolution 1080p` | 仅 2.0-fast/mini 最高 720p；2.5 支持 1080p |
| 脚本拒绝 2.5 首帧非 adaptive | 改 `--ratio adaptive`（画幅锁首帧） |
| 脚本拒绝仅音频参考 | 改 `--model doubao-seedance-2-5-260628` |
| 想批量找历史任务 | `list-tasks --status succeeded --model doubao-seedance-2-5-260628` |
| `401` | API Key 无效或权限未开通 Seedance |
| `403` | 内容审核未通过，检查是否含人脸或违规内容 |
| `429` | 限流或余额不足 |
| 任务 `failed` | 查看 `manifest.json` 中的 `error` 字段 |
| 视频 URL 下载失败 | URL 24 小时过期，尽快下载 |
| `GET /tasks/{id}` 返回 404 | 任务 ID 已过 7 天保留期；用 `list-tasks` 找最近 7 天的任务 |
| 脚本拒绝本地视频路径 | 视频不支持 base64；先上传到公网 URL / TOS，或录入 asset:// 素材库 |
| `--enable-web-search` + 多模态被脚本拒绝 | web_search 仅纯文本输入；如需引用搜索结果，先用纯文本跑一次再以视频为参考续写 |

## 辅助脚本（高级/评测）

| 脚本 | 用途 |
|---|---|
| `scripts/grade_seedance_video.py` | 对 `evals/` 中定义的 eval case 跑出的 outputs 打标，用于 prompt/参数回归测试 |
| `scripts/benchmark_seedance_concurrency.py` | 自适应步进式并发容量测试，测量账号的 running 上限和饱和点 |

正常生产使用不需要跑这两个脚本；调参、跑基准、回归测试时使用。

## 与项目其他 skill 的关系

Seedance 是原子能力 skill：**输入是 prompt + 可选素材 + 参数，输出是视频文件**。它不主动调用其他 skill 准备素材，也不做后期剪辑/发布。

- **上游**（给 Seedance 喂素材的 skill）：
  - 需要首帧/概念图：由调用方自行准备，可用 `article-illustration` / `seedream-image-gen` / `gpt-image-2` 等生图 skill，但具体选择是上层编排的事
  - 需要 BGM/音效/旁白音频：由调用方准备，可用 `volcengine-bigmusic-bgm` / `volcengine-tts`
  - 长视频分镜、多 shot 编排、首尾帧链式续写：应由专门的长视频编排 skill 负责（当前 repo 尚未有），它负责拆 shot、准备素材、调用 Seedance、拼接
- **下游**（消费 Seedance 产出的 video.mp4 的环节；剪辑/发布/归档类 skill 随 [writing-agent-harness](https://github.com/eriklee1895/writing-agent-harness) 项目提供，不在本 repo）：
  - 剪辑/拼接/加字幕 → writing-agent-harness 的 `article-video-clip`
  - 视频插入微信公众号 → writing-agent-harness 的发布工作流
  - 任务收尾归档 → writing-agent-harness 的 `writing-task-closeout`
