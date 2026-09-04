# Seedance 2.5 vs 2.0

来源：火山方舟公开文档（[教程 2607688](https://www.volcengine.com/docs/82379/2607688)、[提示词 2607689](https://www.volcengine.com/docs/82379/2607689)、[创建任务 1520757](https://www.volcengine.com/docs/82379/1520757)）。同一套 `POST/GET/DELETE /contents/generations/tasks`。

## 模型 ID

| 模型 | ID | 备注 |
|---|---|---|
| **2.5** | `doubao-seedance-2-5-260628` | GA（API 约 2026-08-07）。**无 fast / mini** |
| 2.0 standard | `doubao-seedance-2-0-260128` | **唯一 4k** |
| 2.0 fast | `doubao-seedance-2-0-fast-260128` | 最高 720p，更便宜 |
| 2.0 mini | `doubao-seedance-2-0-mini-260615` | 最高 720p，批量最便宜 |

本 skill **默认 2.5**。用户明确要 2.0 / 即梦 2.0（没说 fast/mini）→ standard。只要 4k、没有 2.5 独有需求（30s、整数秒硬切、仅音频、omni 编辑/延长、mov）→ 直接 2.0 standard + 4k，并告知「4k 只能 Seedance 2.0 standard，2.5 最高 1080p。」两者都要 → 停下来让用户选 A) 4k+2.0（≤15s）或 B) 2.5+1080p，不要猜。便宜预览/批量才 fast/mini。

## 能力对照

| 维度 | 2.0 | 2.5 |
|---|---|---|
| 时长 | 4–15s / `-1` | **4–30s** / `-1`（官方 duration 默认 `-1`；本脚本 CLI 默认仍 5） |
| 分辨率 | std: 480/720/1080(8bit)/4k(10bit HEVC)；fast/mini ≤720p | **480p(8bit)、720p(8bit)、1080p(10bit HEVC)**；**无 4k** |
| 480p 16:9 像素 | 864×496 | **854×480**（其余 720p/1080p 像素与 2.0 相同） |
| ratio | 六档 + adaptive；**官方默认 adaptive**（2026-06 省略参数实测出 16:9，系 adaptive 对中性 prompt 的落地结果）；CLI 文生显式传 16:9 | 同样六档 + adaptive；官方默认 adaptive。CLI 文生仍显式传 16:9 |
| 格式 | 仅 mp4 | **mp4 + mov**（mov = H.264 + yuv444p + PCM，后期友好） |
| 参考上限 | 图9+视3+音3，共15 | **图30+视10+音10，共50**；音/视频总时长 30s |
| 仅音频参考 | ❌ 必须配图或视频 | **✅ 允许**（Ark live create+succeeded）。参考须有语义；纯正弦几乎不驱动画面 |
| 首尾帧 ratio | 可指定；建议 adaptive 防跳变 | **必须 adaptive**（锁到首帧画幅），否则 HTTP 400 |
| 编辑 | 较松 | **ratio=adaptive 且 duration=-1**；成片时长≈源片；参考视频 4–30s |
| 延长 | 总时长建议 ≤15s | ratio **必须 adaptive**；`--duration` = **成片总时长**（不是再延长 N 秒）；建议 mov 进出 |
| 新参数 | 无 | `omni_reference_task_type`、`output_format` |
| 时间戳 | 不响应，只认镜头序号 | **响应整数秒**（`0-3s`、`[1s-4s]`、`第 5s`） |
| 多视图 / 自由宽高比 | 固定六档 | 输入素材可出 **[0.4, 2.5]** 任意比（adaptive） |
| web_search | ✅ 仅纯文本 | ✅ 同样 |
| 计费（元/百万 token，官方 1544106） | 480p/720p：刊例 46 / 28（无视频/含视频输入）；1080p：51 / 31；4k：26 / 16；fast 刊例 37/22、mini 刊例 23/14（两者 2026-09-07 前限时 75 折 / 4 折，到期回刊例） | 480p/720p：**70 / 42**；1080p：**77 / 46**（1080p 限时 72 折至 2026-09-17）；无免费额度；开通门槛同 2.0（余额≥200 或资源包）。官方 5s 720p 文生示例 ¥7.56 |
| 并发（官方） | 企业 600 RPM / 10 concurrent；4k RPM 15 / running 1 | 与 2.0 非 4k 相同；**无 4k 档** |
| 人脸 | 禁止真人人脸输入（asset:// / 授权 / 信任产物除外） | 同样 |

## 任务类型硬限制（2.5）

模型按素材 + prompt 判定类型。不符会异步失败（`InvalidParameter.TaskTypeConstraint` / `TaskTypeMismatch`）。

| 类型 | 触发 | 硬限制 |
|---|---|---|
| 文生 | 仅 text | ratio/duration 无特殊限制 |
| 首帧/首尾帧 | `role=first_frame/last_frame` | **ratio 必须 adaptive** |
| 参考生视频 | ≥1 个 `reference_*` | 无特殊限制 |
| 编辑 | ≥1 `reference_video` + 编辑意图（增加/删除/修改/替换） | **ratio=adaptive，duration=-1**；参考视频 4–30s |
| 延长 | ≥1 `reference_video` + 延长意图（向前/向后延长、延续、续写） | **ratio 必须 adaptive**；`--duration` = **成片总时长**（不是再延长 N 秒）；建议 mov 进出 |
| 无缝转场（补间隙） | ≥2 `reference_video` + 衔接意图（"把视频1和视频2衔接起来"） | live 实测：`auto` + `adaptive` + `duration -1` 通过，成片时长≈输入视频时长之和（两 4s → 8.06s）；无需显式 omni 标志。句式见 cookbook §16 |

`omni_reference_task_type`：

- 不传或 `auto`：创建后异步校验（失败浪费排队时间）
- `edit` / `extend`：创建时同步前置校验（脚本也会 client 侧拦截）
- `reference`：明确走参考生视频，避免被判成编辑

脚本：`--omni-reference-task-type`、`--output-format`。未指定则不写入 payload（API 默认 mp4 / auto）。

## Prompt 增量（2.5）

完整写法 → [prompt-guide.md](prompt-guide.md) **§2–3**（2.0 镜头序号 → 附录 A）。此处只记和 2.0 的差：

- 整数秒时间戳，区间必须连续；不要用时间戳写频率。
- 分段：`GLOBAL STYLE` + `Shot N` + `Hard cut.` + named locks。Hard cut 靠**景别**比靠运镜动词更有效。
- 负向音频：`不要字幕`、`无 bgm`、`不要任何声音`。
- 关键帧 / 宫格 / 白模 / 仅音频参考：prompt-guide §3。
- 2.0 继续用「镜头1/2/3」，不要写精确秒数。

## 不兼容点

| 行为 | 结果 |
|---|---|
| 2.5 + `--resolution 4k` | 脚本拒绝。无 2.5 独有需求 → 改 2.0 standard + 4k；否则问用户（4k+2.0 vs 2.5+1080p） |
| 2.5 + 首帧 + `--ratio 9:16`（或其它非 adaptive） | 脚本拒绝；先把图裁到目标画幅再 `adaptive` |
| 2.5 编辑 + 指定 duration | 脚本拒绝；必须 `-1` |
| 2.0 + `--output-format mov` | 脚本拒绝 |
| 2.0 + `--omni-reference-task-type` | 脚本拒绝 |
| 2.0 + 仅 `--reference-audio` | 脚本拒绝；改 2.5 |
| 2.0 + duration 16–30 | 脚本拒绝 |
| 2.5 无 cheap 变体 | 预览请显式 `--model doubao-seedance-2-0-fast-260128` |

`frames` / `seed`（入参）/ `camera_fixed` / `draft` 两代都不接受。

## 怎么吃满 2.5（不要只换 model id）

1. 超过 15s、要秒级剪辑点、仅音频、>9 图、白模/宫格/关键帧、精确编辑/延长、mov 后期 → **必须 2.5**。
2. 多切镜 / 跨镜锁脸：按 [prompt-guide.md](prompt-guide.md) §2 写，不要只换 model id 仍写一句话。
3. 跨镜头不换脸：参考图锁身份，比纯文字稳；每人一份清晰特写脸，全身板去脸。
4. 50 参考是天花板：一个稳定元素一份素材。堆满会更糊。
5. 30s 是上限不是目标。一次只改一个变量。10–15 次仍烂就拆场景。
6. 编辑/延长显式 `--omni-reference-task-type`，避免任务启动后才异步报 `TaskTypeConstraint`。延长的 `--duration` 是成片总时长。

## 网关差异（OpenMontage 注意）

OpenMontage 的 fal.ai / Runway / Comfy 路径常把 2.5 写成 **仅 480p/720p**，且 Ark 适配器默认仍是 2.0 standard、拒绝仅音频、未暴露 `omni_reference_task_type` / `output_format`。**本 skill 走火山方舟官方 API**：2.5 支持 **1080p 10-bit HEVC**、允许仅音频、有 mov 与 omni 任务类型。不要把网关限制抄进 Ark 调用。

## CLI 与官方默认的差异（有意保留）

| 参数 | 官方 2.5 API 默认 | 本脚本 CLI 默认 | 原因 |
|---|---|---|---|
| `model` | — | 2.5 | 质量默认走新模型 |
| `duration` | `-1` | `5` | 避免意外生成 30s 账单 |
| `ratio` | `adaptive` | `16:9` | 文生可复现；首帧必须自己改 adaptive |
| `resolution` | `720p` | `720p` | 一致 |
| `output_format` | `mp4` | 不传 | 一致 |

## 实测（2026-09-03，火山方舟 live API）

两轮 create + poll 到终态。不要把网关（fal / OpenMontage 适配器）的 720p、拒仅音频抄进 Ark。

### 第一轮（2.5 文生 / 格式 / 1080p / 首帧翻车）

四路并行约 2.4 min 全部 succeeded。模型 `doubao-seedance-2-5-260628`。

| 请求 | 结果 | tokens | 墙钟 |
|---|---|---|---|
| 文生 4s 480p 16:9 mp4 | succeeded，854×480 | 38,830 | ~2–2.5 min |
| 文生 4s **1080p** 16:9 | succeeded（**Ark 支持 1080p**） | 196,425 | 更久 |
| 文生 4s 480p **`--output-format mov`** | succeeded，URL `.mov` | 38,830 | 同 4s 480p |
| 文生 4s 480p，prompt 含 `0-2s`/`2-4s` | succeeded | 38,830 | 同 4s 480p |
| 首帧 + `ratio=16:9`（绕过脚本） | **HTTP 400** `InvalidParameter.TaskTypeConstraint`：输出比例跟首帧图 | 不计费 | — |

480p 4s 三路 token 完全相同。1080p 约为 480p 的 **5×**。

### 第二轮（补齐 2.5 独特能力 + 2.0-fast 回归）

全部 create 成功后 poll 到 `succeeded`。2.5 480p 16:9 像素确认 **854×480**。

| 请求 | 结果 | tokens | 墙钟（created→updated） | 成片 |
|---|---|---|---|---|
| **2.0-fast** 4s 480p 1:1 | succeeded（2.5 改动未破坏 2.0 路径） | 38,800 | ~75s | 640×640 mp4 |
| **仅音频** `--reference-audio` 3s wav + 文生 4s 480p | succeeded。**官方「2.5 允许仅音频」在 Ark 为真**，脚本不拦截 | 38,830 | ~137s | 854×480；输出音轨是模型重做的，不是 440Hz 正弦。纯音几乎不驱动画面 |
| 首帧 + **`--ratio adaptive`** 4s 480p | succeeded。响应 `ratio=427:240`（锁 2560×1440 源图） | 38,830 | ~224s | 854×480，无音轨（`--no-generate-audio`）；首帧身份锁住，prompt 里的蒸汽加在字上 |
| 编辑 `--omni-reference-task-type edit --ratio adaptive --duration -1` | succeeded。响应 `duration=16`（源片 16.83s）、`ratio=363:290` | 322,800 | ~214s | 726×580；路人变少，但「保持运镜」未锁死，中段长出新主角 |
| 延长 `--omni-reference-task-type extend --ratio adaptive --duration 8` | succeeded。响应 `duration=8`、`ratio=363:290`（源 1350×1080 / 5.1s） | 138,166 | ~148s | 726×580 / **8.00s**。**duration = 成片总时长**，不是再延长 8 秒。弱 prompt「延续同一场景」整段换景；必须写「紧接@视频1结尾：具体动作」 |
| 文生 **16s** 480p 16:9 | succeeded。确认 2.5 **长于 15s** | 154,120 | ~179s | **16.06s** 854×480 |
| GLOBAL STYLE + Hard cut + `0-4s/4-8s/8-12s` **12s** | succeeded | 115,690 | ~162s | 12.06s；**4s 硬切切到旗帜特写**，8s 升机位部分兑现 |
| 2.5 + `--resolution 4k` dry-run | **脚本拒绝**（未打 API） | — | — | 提示改 1080p 或改 2.0 standard |

### Token / 延迟启发式（同一账号，480p 除非另注）

- 2.5 文生 480p：`≈ 38830 × (duration/4)`。12s=115,690、16s=154,120，近似线性。
- 2.5 1080p 4s = 196,425 ≈ 480p 的 5×。
- 带 **reference_video** 的编辑/延长远贵于同时长文生（编辑 16s=322,800；延长 8s=138,166）。
- 2.0-fast 4s 480p token **≈ 2.5 文生**（38,800 vs 38,830）。fast 便宜在 **2.0 单价**，不是 token 腰斩。
- 墙钟大致随时长和是否吃视频参考上升；首帧 4s 可比纯文生更慢。

### 脚本不改拦截的结论

- 仅音频：**不要** client 拒绝 2.5；继续只拦 2.0。
- 2.0-fast / 显式 `--model`：保持可调用。
- 2.5+4k、2.5 首帧非 adaptive、2.5 编辑非 `adaptive`+`duration=-1`：继续拦。

### 第三轮（2026-09-04：模型矩阵回归 + 2.5 新能力补测）

同 prompt 4 模型 batch + 3 个 2.5 能力验证，全部 succeeded。

| 请求 | 结果 | tokens | 墙钟 / 成片 |
|---|---|---|---|
| 4 模型矩阵同 prompt（4s 480p 16:9，2.5/2.0/fast/mini 并行 batch） | 4/4 succeeded | 2.5 **38,830**；2.0 / fast / mini 均 **40,594** | — |
| 30s 三镜时间戳文生（480p，无音频） | succeeded，三镜结构按 0-10/10-20/20-30 分段 | **288,625**（≈ 4s 的 7.4×） | 193s；成片 **30.04s** 854×480 |
| **时间戳局部编辑**：`@视频1 把 0-2s 从晴天改为雨天…其余保持不变`，`edit` + mov | succeeded。**入片 4.04s、成片 4.04s——2.5 自产片做编辑输入 0 误差**（官方称一般 ±0.3~0.4s） | 77,260 | 142s；mov 实测 `h264` + `pcm_s16le`（PCM 无损音轨） |
| **无缝转场**：两段成片 `@视频1`+`@视频2` + "衔接起来"，auto 任务类型、`adaptive`、`duration -1` | succeeded，自动拼出 8s | 154,120 | 357s；成片 **8.06s**（4.04+4.04，总时长=输入之和） |
| batch-submit `output_format: mov` 两 shot | 2/2 succeeded | — | 下载文件扩展名按 URL 判定为 `.mov`（脚本修复，旧版恒存 `.mp4`） |

第三轮新增结论：

- **无缝转场（视频补间隙）走 auto 即可**：两段参考视频 + `ratio adaptive` + `duration -1`，模型自动按输入总时长出片（两 4s 片 → 8.06s）。无需 edit/extend 标志。
- **局部编辑可按时间戳圈范围**："把 0-2s 改为 X，其余保持不变" live 通过——这是 30s 广告"片段重拍"的能力基础（哪段坏改哪段，不用整片重抽）。
- **2.5 自产片回灌编辑/延长 = 零时长误差**（官方承诺，live 证实）；非 2.5 来源片预期 ±0.3~0.4s。
- **模型矩阵确认完整**：官方模型列表（1330310，2026-09-02 更新）2.x 在列仅本 skill 支持的 4 个 ID，无 2.5 lite/turbo/fast、无更新的 2.x；1.5-pro 已标注"即将下线"，1.0 系列本 skill 明确不支持。
- **2.5 产物 video_url 下载上限 100 次**（官方 1521309；URL 仍 24h 有效）。

