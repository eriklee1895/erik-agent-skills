# Seedance 2.5 Draft 模式

Draft 是 **Seedance 2.5 专属**的创意预览和挑片流程：先以 480p 检查镜头方向，确认后从相同 Draft task ID 生成原生 1080p。它更适合提前验证场景结构、构图、主体动作、运镜和节奏；不适合用来确认 1080p 才看得清的小字或细纹理。

## 什么时候用

| 用户意图 | 建议 |
|---|---|
| 明确要 Draft，或要比较多个 2.5 镜头后选一个做 1080p | 直接生成 Draft 样片 |
| 明确只要一个 1080p 终稿，且方向已定 | 直接生成 1080p |
| 目标是 480p / 720p | 按目标分辨率普通生成 |
| 要 4k | 使用 2.0 standard；2.0 不支持 Draft 升版 |
| 可能反复试镜头，但用户没说是否接受先审片 | 只问一次「先看 480p Draft 再选 1080p，还是直接生成 1080p？」 |

不要把 Draft 描述成保证更快的生成模式。它降低预览成本，给用户更早的视觉反馈；服务端排队和生成时长仍会波动。2026-09-23 的四候选并行实测中，Draft 服务端耗时中位数为 74.5 秒，直接 1080p 为 60.5 秒，未测得速度优势。

## HITL 放在样片之后

用户明确要求 Draft 时，直接生成第一轮样片。完成后展示可播放视频、task ID 和观察到的画面问题，让用户选择：

1. 保留这个方向并升版；
2. 指定一个修改维度，再创建一条 Draft；
3. 放弃这个方向。

改 prompt 或素材必须创建新的 Draft task，旧 Draft ID 始终绑定旧输入。用户已明确授权自动挑选时，可以自行比较 Draft 并升版。

## 操作流程

### 生成一个 Draft

`--draft` 默认自动使用 480p。任务成功后 CLI 会下载视频和 manifest；从 manifest 取 `task_id`，先查看样片，再决定是否升版。

```bash
uv run scripts/generate_seedance_video.py \
  --draft \
  --prompt "红纸船顺着林间溪流漂过，低机位跟拍，阳光在水面闪动" \
  --duration 4 --ratio 16:9 --no-generate-audio
```

### 用户选中样片后生成 1080p

```bash
uv run scripts/generate_seedance_video.py promote-draft \
  --task-id cgt-20260923xxxxx-xxxx
```

`promote-draft` 会查询来源任务，要求其 7 天内已成功且 `draft=true`，随后提交升版并默认等待、下载终稿。`--create-only` 只提交终稿任务并返回新的 task ID。Draft ID 从 `created_at` 起有效 7 天；视频 URL 有效 24 小时，样片和成片都应及时下载。

### 批量候选

为独立镜头或方案准备 shots JSON 后，`batch-submit --draft --wait` 会并行生成并下载 480p Draft。可在单个 shot 中用 `"draft": true/false` 覆盖批量默认值。批量 Draft 的升版按用户选中的 task ID 逐条执行。

## 成本与价值

Draft 480p 按普通 480p 视频的 token 用量和单价计费；升版 1080p 按普通 1080p 推理计费。若生成 `N` 个候选，只升版一个：

```text
Draft 路径 = N × 480p + 1 × 1080p
直接路径   = N × 1080p
```

只出一条时，Draft 会额外增加一条 480p 成本；多个候选中只为选中的一个升版，才节省反复生成 1080p 的费用。

在 2026-09-23 的四候选实测中，4 条 480p Draft + 1 条 1080p 升版共 351,745 tokens；直接生成 4 条 1080p 共 785,700 tokens，少 55.23%。按当日公开刊例价估算为 ¥25.9971 对 ¥60.4989，约省 ¥34.5018（57.03%）。这是基于 API `usage` 和公开单价的估算，不是账号账单的逐任务实扣；套餐和折扣会影响实际价格。

被升版任务会继承原 Draft 的模型、prompt、素材、seed、音频设置、ratio 和 duration。升版是再次推理，主体、构图和运动方向在实测样例中得以延续，细节仍会改变；不要把它当作逐像素超分。升版请求的禁止字段和允许重设字段见 [api-reference.md](api-reference.md#draft-升版请求的字段边界)。

完整数据、逐任务 ID、耗时口径及测试限制见 [Draft 模式价值实测报告](../evals/draft-mode-value-2026-09-23.md)。官方说明见[Seedance 2.5 教程](https://docs.volcengine.com/docs/ark/seedance-2-5)和[模型价格表](https://docs.volcengine.com/docs/ark/model-pricing)。
