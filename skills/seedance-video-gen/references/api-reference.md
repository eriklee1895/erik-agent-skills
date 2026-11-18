# Seedance 2.5 系列 API

核对日期：2026-11-18。只维护标准版与 flash。服务基址 `https://ark.cn-beijing.volces.com/api/v3`；请求使用 `Authorization: Bearer $ARK_API_KEY`，JSON 请求使用 `Content-Type: application/json`。

## 创建任务

`POST /contents/generations/tasks` → `{"id":"cgt-..."}`。

```json
{
  "model": "doubao-seedance-2-5-260628",
  "content": [{"type": "text", "text": "黄昏海岸，镜头缓慢推进。无 bgm，只保留海浪声。"}],
  "duration": 5,
  "ratio": "16:9",
  "resolution": "720p",
  "generate_audio": true,
  "watermark": false
}
```

只有用户明确要求 flash 才替换 model 为 `doubao-seedance-2-5-flash-261115`；其输出只支持480p/720p，且无 Draft。

| 字段 | 规则 |
|---|---|
| model | 必填；本 skill 仅接受上述两个完整 Model ID |
| content | 必填数组，文本/图片/视频/音频或标准版的 draft_task |
| resolution | 默认720p；标准版480p/720p/1080p/4k，flash480p/720p；1080p/4k为10-bit（实测MP4为HEVC 10-bit，480p/720p为H.264 8-bit；MOV为H.264+yuv444p+PCM） |
| ratio | 默认adaptive；16:9/4:3/1:1/3:4/9:16/21:9/adaptive |
| duration | 默认-1；整数4–30或-1；CLI 默认5。编辑输出与源片基本一致，可为非整数秒；官方不同章节给出约0.3–0.4 秒误差说明，并称2.5自产源无此差距（实测2.5 flash自产源仍短约0.33秒）。`8n+1`只能作为官方建议尝试；严格等长优先参考生成+显式duration，并用ffprobe检查媒体元数据；查询返回时长仍为约数 |
| generate_audio | 默认true，生成同步音轨；false生成无声视频 |
| output_format | 默认mp4；可选mov（H.264+yuv444p+PCM，推荐编辑/延长） |
| omni_reference_task_type | 默认auto；reference/edit/extend；显式指定会提前校验，但实际意图仍需匹配 |
| draft | 默认false；**仅标准版**支持true，分辨率必须480p |
| return_last_frame | 默认false；尾帧为JPEG，无水印、宽高同视频，URL见查询响应 |
| watermark | 默认false；true在右下角显示AI生成水印 |
| priority | 默认0，整数0–9，仅同Endpoint内排队顺序 |
| tools | `[{"type":"web_search"}]`；只支持一个text的纯文本输入，由模型决定调用次数 |
| execution_expires_after | 默认172800秒；3600–259200秒，从created_at计算，超时expired；CLI未暴露 |
| callback_url | 任务状态变化时POST通知；不是仅成功时回调；CLI未暴露 |
| safety_identifier | 最多64字符、固定唯一的英文终端用户标识；推荐哈希用户名/ID/邮箱，勿传原始隐私值；CLI未暴露 |

**不支持的请求字段**：frames、seed、camera_fixed、service_tier=flex。seed可在响应返回，但不能作为本系列入参复现。参数写入JSON字段，不在prompt末尾使用弱校验 `--rs` 等方式。

### content 类型与组合

| type | 数据字段 | role |
|---|---|---|
| text | text | 不设置 |
| image_url | image_url.url | first_frame / last_frame / reference_image |
| video_url | video_url.url | reference_video |
| audio_url | audio_url.url | reference_audio |
| draft_task | draft_task.id | 不设置；仅标准版升版 |

首帧模式：一张first_frame；首尾帧模式：一张first_frame加一张last_frame。不得单独传last_frame。首帧/首尾帧与reference_*互斥；要多模态并近似指定首尾帧，用reference_image并在prompt绑定，不能承诺严格对齐。

多模态：标准版≤30图/10视频/10音频；flash≤10图/5视频/5音频。两款均可仅音频；文本在API层可省略，本CLI要求prompt。视频总时长≤30秒，音频总时长≤30秒；数量合规不代表总时长合规。

传输：图/音频可公网URL、data URL、asset://；视频只支持公网URL、asset://。`file-...`不是素材ID，Files API关系见 [files-api.md](files-api.md)。格式、体积、像素限制见 [multimodal-reference.md](multimodal-reference.md)。

### 任务锁定

两模型共用：首帧/首尾帧必须ratio=adaptive；编辑需reference_video、ratio=adaptive、duration=-1，待编辑视频4–30秒；延长需reference_video、ratio=adaptive，duration为成片总长。`omni_reference_task_type`不能代替prompt中的编辑/延长意图。

### Draft 升版请求的字段边界

仅标准版，来源必须成功且draft=true；model与来源一致，resolution为1080p或4k，draft省略或false：

```json
{
  "model": "doubao-seedance-2-5-260628",
  "content": [{"type": "draft_task", "draft_task": {"id": "cgt-xxx"}}],
  "resolution": "1080p"
}
```

禁止重传text、参考图/视频/音频、duration、ratio、seed、generate_audio、omni_reference_task_type；由服务端继承。可重设return_last_frame、output_format、watermark、execution_expires_after、priority、callback_url、safety_identifier，省略时使用模型默认值，不继承来源。教程也列出service_tier可重设，但本系列不支持flex，勿据此启用离线模式。

升版时可选择 `resolution=1080p` 或 `resolution=4k`，CLI 默认1080p。

Draft从2026-10-28 10:00（UTC+8）起新建ID有效14天，之前ID仍7天。两次任务独立计费；成片token单价按Draft原始请求是否有视频确定，输入时长仅计算原始参考视频，不把Draft视频重复计入。操作见 [draft-mode.md](draft-mode.md)。

## 查询与下载

`GET /contents/generations/tasks/{id}`。

| 字段 | 含义 |
|---|---|
| id/model/status | 任务标识、实际模型、状态 |
| content.video_url | 成功视频URL；24小时有效、最多下载100次 |
| content.last_frame_url | 请求尾帧时返回；24小时有效、最多下载100次，及时下载 |
| duration/ratio/resolution/output_format | 实际生效输出参数；adaptive比例可返回非预设比值 |
| framespersecond | 响应中的实际输出帧率；本 skill 实测 480p/720p/1080p/4K/编辑/延长均为 24fps，其他规格仍以字段为准 |
| generate_audio | 是否生成音频 |
| seed | 服务端实际使用种子，只读 |
| draft/draft_task_id | 区分标准版样片、升版及来源 |
| usage.completion_tokens/total_tokens | 生成计费用量，成功后据实际usage算费用 |
| usage.tool_usage.web_search/tools | 搜索次数及实际工具调用 |
| created_at/updated_at | Unix秒 |
| safety_identifier | 创建时提供的终端用户标识原样返回 |
| execution_expires_after/priority/service_tier | 超时、优先级、实际服务等级 |
| error | 失败的code和message |

状态：queued → running → succeeded/failed；queued可取消为cancelled；排队或运行超时为expired。脚本为兼容接受completed，但官方状态名为succeeded。本地max-wait超时不取消服务端任务。

其他任务ID保留7天，cancelled任务仅保留24小时；Draft按上述7/14天规则。视频与尾帧URL仍只有24小时。`duration`按实际帧率换算向下取整，是约数；精确片长看下载媒体元数据。

## 查询列表

`GET /contents/generations/tasks`。

| Query | 规则 |
|---|---|
| page_num/page_size | 默认1/20，各1–500 |
| filter.status | queued/running/succeeded/failed/cancelled/expired |
| filter.model | 精确筛选推理Endpoint ID（`ep-...`），不是doubao模型ID；CLI用`--endpoint-id` |
| filter.task_ids | 多ID重复同名参数，例如 `filter.task_ids=cgt-a&filter.task_ids=cgt-b` |
| filter.service_tier | 默认default；历史flex任务需显式传flex，本系列生成不能启用flex；CLI未暴露 |

响应为total和items，items字段与单任务查询一致。cancelled任务仅保留24小时，其他留存期按任务类型区分，不能把Draft一律当7天。轮询使用单任务端点，避免用列表逐条轮询；账号级上限为单任务查询20 QPS、任务列表1 QPS、取消或删除20 QPS。创建与running限额见 [key-constraints.md](key-constraints.md#联网搜索与配额)，并服从账号/Endpoint最新配额。

## 取消或删除

`DELETE /contents/generations/tasks/{id}`，成功HTTP200，返回空对象。

| 当前状态 | 结果 |
|---|---|
| queued | 取消排队，变为cancelled |
| running | 不支持 |
| succeeded/failed/cancelled/expired | 删除记录，之后不能查询 |

## 错误与计费

参数错误检查模型×分辨率、数量、模式互斥、ratio/duration锁定。同步参数错误不会创建任务；异步 `TaskTypeConstraint` / `TaskTypeMismatch` 需结合prompt和omni类型检查。401查密钥，403看实际审核/权限错误，404查ID与有效期；429降低请求频率、检查返回错误，不把所有429都当余额不足。图片输入被隐私检测拦截时返回 `InputImageSensitiveContentDetected.PrivacyInformation`，应改用非真人、虚拟人像或已授权素材。

按completion_tokens与实时单价计费，仅成功任务计费；含参考视频时存在最低用量限制。token估算受输入视频时长、输出时长、分辨率与帧率影响；不能把「flash成本降低34%」当token数固定减少34%——实测同请求token数相同，34%来自官方单价差（480p/720p文生46 vs 70元/M token）。价格见[实时价格页](https://console.volcengine.com/ark/region:cn-beijing/docs/model-pricing)。

脚本使用httpx直调；临时HTTP错误有退避重试。创建任务POST没有文档化的幂等键，连接中断后结果不明时可能已经创建任务；再次提交前结合已保存ID和列表核对，避免盲目重跑整批。

## 本地记录

manifest保存task_id、模型/实际参数、status/error、usage、seed、draft/draft_task_id、服务端时间、request_payload与下载路径。普通生成写prompt.md；升版请求不含prompt，需从原Draft输出目录保留。URL和data URL属于运行时数据，输出目录不要提交到技能仓库。

## 官方来源

- [创建任务](https://console.volcengine.com/ark/region:cn-beijing/docs/create-video-generation-task-api)
- [查询任务](https://console.volcengine.com/ark/region:cn-beijing/docs/get-video-generation-task-api)
- [查询列表](https://console.volcengine.com/ark/region:cn-beijing/docs/list-video-generation-tasks-api)
- [取消或删除](https://console.volcengine.com/ark/region:cn-beijing/docs/cancel-or-delete-video-generation-tasks-api)
- [系列教程](https://console.volcengine.com/ark/region:cn-beijing/docs/seedance-2-5)

上述文档地址在官方 `ark.volcengine.com` 文档域名追加 `.md` 可获取Markdown正文。维护时先核对当前官方版本，再调整约束；不把平台旧版模型参数混入本skill。
