# 火山引擎豆包 ASR API 参考（录音文件识别）

> 摘录自官方文档（2026-09 拉取），agent 调脚本即可，以下仅供排错/扩展参数时参考。
> 鉴权与 TTS 相同：语音控制台单 API Key（`VOLC_SPEECH_API_KEY`），与火山方舟 ARK key **不通用**。

## 两个接口

| | 极速版（默认） | 标准版（兜底） |
|---|---|---|
| 端点 | `POST /api/v3/auc/bigmodel/recognize/flash` | `POST /api/v3/auc/bigmodel/submit` + `/query` |
| Resource-Id | `volc.bigasr.auc_turbo` | `volc.seedasr.auc`（2.0）/ `volc.bigasr.auc`（1.0） |
| 调用方式 | 一次请求同步返回 | 提交后轮询（请求体空 JSON `{}`） |
| 音频传入 | `audio.data`（base64）或 `audio.url`。data 直传正式记载于极速版旧文档树（1631584，"上传文件二进制流"）；**2026-08 更新的新文档树（2608628/2606791/2606792）只文档化了 `audio.url`**。但 data 直传实测在极速版和标准版 submit 上均可用（2026-09 验证；生态内多个生产项目依赖），属"文档不写但服务端支持"。脚本两种都支持：本地文件默认 data 直传，http(s) 输入走 url | 同左；data 直传无文档但实测可用（volc.seedasr.auc，2026-09 验证） |
| 时长/大小 | ≤ 2h / ≤ 100MB（base64 建议 ≤20MB） | ≤ 5h / ≤ 512MB |
| 音频格式 | WAV / MP3 / OGG OPUS | wav/mp3/ogg/pcm/spx/amr/aac/m4a |
| 计费/开通 | 需单独开通 `volc.bigasr.auc_turbo` | 需单独开通；单价更低 |

服务根地址：`https://openspeech.bytedance.com`

## 请求头

| Header | 值 |
|---|---|
| `X-Api-Key` | 语音控制台 API Key（新版控制台单头；旧版控制台用 `X-Api-App-Key` + `X-Api-Access-Key` 双头） |
| `X-Api-Resource-Id` | 见上表 |
| `X-Api-Request-Id` | 随机 UUID；标准版中它就是 task_id，查询时复用同一个 |
| `X-Api-Sequence` | 固定 `-1` |
| `Content-Type` | `application/json` |

## 请求体（flash / standard 共用形状）

```json
{
  "user": { "uid": "任意调用方标识" },
  "audio": {
    "data": "<base64，flash 本地上传>",
    "url":   "<公网音频链接，标准版必填 / flash 可选>",
    "format": "mp3",
    "language": "zh-CN"
  },
  "request": {
    "model_name": "bigmodel",
    "enable_itn": true,
    "enable_punc": true,
    "enable_ddc": false,
    "show_utterances": true,
    "enable_speaker_info": true,
    "ssd_version": "200",
    "corpus": { "context": "{\"hotwords\":[{\"word\":\"豆包\"}]}" }
  }
}
```

注意：`corpus.context` 是**序列化为 JSON 字符串**的对象（不是嵌套对象）。
flash data 模式下不发 `audio.format`（服务端从字节流嗅探）。

### 常用 request 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `model_name` | — | 必填，固定 `bigmodel` |
| `enable_itn` | true | 口语数字/金额/日期 → 书面形式（"一九七零年"→"1970 年"） |
| `enable_punc` | true | 加标点 |
| `enable_ddc` | false | 语义顺滑（删语气词/重复）——**出字幕建议 false 保真** |
| `show_utterances` | false | 返回分句/分词时间戳、说话人；**出字幕必须 true** |
| `enable_speaker_info` | false | 说话人分离；需 `show_utterances=true`；仅中文/自动语种生效 |
| `ssd_version` | — | `200`：≤5 人非会议场景；`300`：声纹匹配，长会议场景 |
| `enable_channel_split` | false | 双声道识别，结果以 `channel_id` 标记 |
| `vad_segment` | false | true=按 VAD 静音分句；false=按语义分句（默认，字幕更自然） |
| `end_window_size` | 800 | VAD 静音判停阈值 ms，[300,5000]，推荐 800-1000 |
| `enable_auto_lang` | false | 自动语种检测（不与 corpus 热词同用） |
| `enable_emotion_detection` | false | 分句返回 angry/happy/neutral/sad/surprise |
| `enable_gender_detection` | false | 分句返回 male/female |
| `corpus.boosting_table_id` | — | 控制台配置的热词词表 |
| `corpus.correct_table_id` | — | 替换词词表 |
| `sensitive_words_filter` | — | 敏感词过滤（JSON 字符串） |

### `audio.language` 常用值

`zh-CN`（普通话）、`en-US`、`ja-JP`、`ko-KR`、`yue-CN`（粤语）、`id-ID`、`es-MX`、`pt-BR`、`de-DE`、`fr-FR` 等 20+。
**留空时**自动识别：中文、英文、上海话、闽南话、四川话、陕西话、粤语。

## 响应

状态看**响应头**（HTTP 可能恒 200）：

| Header | 含义 |
|---|---|
| `X-Api-Status-Code` | 见下表 |
| `X-Api-Message` | `OK` 或错误描述 |
| `X-Tt-Logid` | 排障用 logid，报错时务必带上 |

状态码：

| Code | 含义 | 处理 |
|---|---|---|
| `20000000` | 成功 | 读 body |
| `20000003` | 静音/无人声 | 视为空结果成功 |
| `45000002` | 空音频 | 同样按空结果处理（参考成熟工具的分类约定） |
| `20000001` / `20000002` | 任务处理中（标准版轮询） | 继续轮询；success code 但 body 无 `result` 也算处理中 |
| `45000001` | 请求参数无效 | 不重试 |
| `45000002` | 空音频 | 不重试 |
| `45000151` | 音频格式不正确 | 不重试；用 ffmpeg 转 mp3 |
| `55000031` | 服务器繁忙/过载 | 指数退避重试 |
| `550xxxxx` | 服务内部错误 | 重试 |
| HTTP 401/403 | API Key 无效/未开通该资源 | 不重试；检查 key 与开通状态 |

成功 body：

```json
{
  "audio_info": { "duration": 6312 },
  "result": {
    "additions": { "duration": "6312" },
    "text": "整段文本",
    "utterances": [
      {
        "start_time": 480, "end_time": 5880,
        "text": "分句文本（含标点）",
        "additions": { "speaker": "1", "channel_id": "1" },
        "words": [
          { "text": "刚", "start_time": 480, "end_time": 600, "confidence": 0 },
          { "text": "刚", "start_time": 680, "end_time": 800, "confidence": 0 }
        ]
      }
    ]
  }
}
```

关键事实（实测 + 文档）：
- 时间单位均为**毫秒**；word 级时间戳在 `utterances[].words[]`。
- **word token 不含标点**，标点只出现在 `utterances[].text`（enable_punc 生成）——脚本已做对齐回填。
- 说话人 ID 在 `utterances[].additions.speaker`，字符串 "0"/"1"/...。
- `confidence` 当前固定返回 0，不代表置信度为零。

## 文档链接

- 极速版 HTTP：https://www.volcengine.com/docs/6561/1631584
- 标准版任务提交：https://www.volcengine.com/docs/6561/2606791
- 标准版结果查询：https://www.volcengine.com/docs/6561/2606792
- 闲时版（24h 内出结果，更便宜）：submit `/api/v3/auc/bigmodel/idle/submit`，resource `volc.bigasr.auc_idle`
- 热词最佳实践：https://www.volcengine.com/docs/6561/2604976
- API Key 管理：https://console.volcengine.com/speech/new/setting/apikeys

## 抽音时间对齐（字幕不漂移的前提）

视频抽音轨必须带 `-af aresample=async=1:first_pts=0`。源音频存在 PTS gap
（录制暂停、多段拼接、转封装丢帧）时，默认抽音（async=0）忽略 PTS 顺序拼接样本，
时间轴被压扁，字幕从中段开始累计漂移（真实案例：31 分钟视频末尾漂 8.5s）。
`async=1` 在 gap 处填静音、overlap 处丢样本，`first_pts=0` 对齐非零起始音轨；
正常无 gap 视频上是 no-op。
