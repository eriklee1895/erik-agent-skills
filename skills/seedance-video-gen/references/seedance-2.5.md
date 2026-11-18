# Seedance 2.5 标准版与 flash

按 2026-11-18 的[官方系列教程](https://console.volcengine.com/ark/region:cn-beijing/docs/seedance-2-5)、[创建任务 API](https://console.volcengine.com/ark/region:cn-beijing/docs/create-video-generation-task-api)与[系列提示词指南](https://console.volcengine.com/ark/region:cn-beijing/docs/seedance-2-5-prompt-guide)维护。

## 选择规则

默认 `doubao-seedance-2-5-260628`。**只有用户明确要求 flash，才用 `doubao-seedance-2-5-flash-261115`**；低价、批量、快出片等描述不会自动切模型。用户已选 flash 而参数超限时，先说明冲突并取得调整方向，不自动回退标准版。

| 能力 | 标准版 | flash |
|---|---|---|
| 定位 | 旗舰视听品质与创作表现 | 接近旗舰效果，侧重速度与成本 |
| 时长 | 4–30 秒 / -1 | 同左 |
| 分辨率 | 480p / 720p / 1080p / 4k | 480p / 720p |
| 输出位深 | 480p / 720p 为 8-bit，1080p / 4k 为 10-bit | 480p / 720p 为 8-bit |
| 输出编码（实测） | MP4：1080p/4k 为 HEVC 10-bit，480p/720p 为 H.264 8-bit；MOV：H.264+yuv444p+PCM | MP4 480p/720p 为 H.264 8-bit |
| 4K 输出 | 支持（10-bit 位深） | 不支持 |
| 参考图片 | ≤30 | ≤10 |
| 参考视频 | ≤10 | ≤5 |
| 参考音频 | ≤10 | ≤5 |
| 视频总时长 / 音频总时长 | 各 ≤30 秒 | 同左 |
| 仅音频参考 | 支持 | 支持 |
| 编辑 / 延长 / 时间戳 | 支持 | 支持 |
| 输出格式 | mp4 / mov | 同左 |
| Draft | 480p → 同模型1080p或4k | 不支持 |
| web_search | 仅纯文本 | 同左 |

flash 的「速度翻倍、成本降低约34%」是定位信息。官方价格页（2026-11-18）显示 480p/720p 文生 token 单价：标准版 70 元/M、flash 46 元/M（约低34%）；含视频输入为 42/28 元/M。实测同请求两者 token 数相同，成本差来自单价；速度不保证固定倍数，实际以任务 `usage`、[实时价格](https://console.volcengine.com/ark/region:cn-beijing/docs/model-pricing)与账单为准。

4K 按输出分辨率单独定价：文生 31 元/M token（输入含视频 19 元/M），5s 16:9 约 30.13 元/个；以价格页为准。

## 任务参数锁定（两款共用）

| 任务 | 输入 / 意图 | 参数 |
|---|---|---|
| 文生 | 纯文本 | 可指定 ratio/duration |
| 首帧 / 首尾帧 | first_frame，或 first_frame+last_frame | ratio 必须 adaptive；时长可指定 |
| 参考生视频 | reference_image/video/audio | 可指定 ratio/duration；仅做语义参考 |
| 编辑 | ≥1 reference_video，prompt 表达增删改 | ratio=adaptive，duration=-1；待编辑视频4–30秒 |
| 延长 | ≥1 reference_video，prompt 表达前/后续写 | ratio=adaptive；duration 是成片总时长 |

`omni_reference_task_type=auto`（默认）由模型判定；显式 `reference/edit/extend` 会在创建时提前校验。实际处理仍结合 prompt 判定；即使前置校验通过，也可能因意图不符异步报 `TaskTypeMismatch`。

全模态参考但**不区分子任务**时，官方推荐 `auto + ratio=adaptive + duration=-1`；含参考视频时建议单段4–30秒。需要明确输出画幅或固定时长的参考生视频仍可指定 ratio/duration；编辑与延长按上表锁定。

两段视频衔接可用 auto + adaptive + duration=-1，并写清视频1→视频2的过渡动作；检查实际输出，不承诺每次均严格等于输入时长之和。

## CLI 与 API 默认值

| 参数 | 官方 API | CLI |
|---|---|---|
| model | 必填 | 标准版 |
| duration | -1 | 5，控制单次生成长度 |
| ratio | adaptive | 16:9；锁定任务需显式 adaptive |
| resolution | 720p | 720p；--draft 时480p；标准版可显式 1080p/4k |
| generate_audio | true | true |
| output_format | mp4 | 不传，遵循 API |
| draft | false | 不传；仅标准版 --draft 传 true |

## Draft 有效期

仅标准版有 Draft；flash 的普通480p/720p视频不具有 Draft 升版资格，也不能把 task ID 换模型升为标准版1080p或4k。

2026-10-28 10:00（UTC+8）及之后创建的 Draft ID 有效14天，更早的仍7天；其他任务 ID 为7天。两阶段参数继承、计费与展示流程见 [draft-mode.md](draft-mode.md)。
