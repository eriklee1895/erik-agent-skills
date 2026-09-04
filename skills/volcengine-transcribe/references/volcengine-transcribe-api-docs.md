# 豆包录音文件识别 2.0 标准版 API 参考

本 Skill 只使用最新标准版模型 `volc.seedasr.auc`。以下内容用于扩展参数和排错；
常规转写直接运行脚本。

## 接口

| 操作 | Endpoint |
|---|---|
| 提交 | `POST https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit` |
| 查询 | `POST https://openspeech.bytedance.com/api/v3/auc/bigmodel/query` |

请求头：

| Header | 值 |
|---|---|
| `X-Api-Key` | 语音控制台 API Key |
| `X-Api-Resource-Id` | `volc.seedasr.auc` |
| `X-Api-Request-Id` | 提交时为客户端 UUID；查询时为提交响应的 `task_id` |
| `X-Api-Sequence` | 提交时为 `-1`；查询接口不需要 |
| `Content-Type` | `application/json` |

成功提交的响应体包含 `task_id`。不要假设客户端生成的 request UUID 与
服务端返回的 `task_id` 相同。保留的旧版 `audio.data` 兼容路径可能返回空的
`{}`，但服务端仍接受提交时的 request UUID 查询；脚本只在缺少 `task_id` 时
使用这个兼容回退。

## 输入

当前文档化的请求使用：

```json
{
  "audio": {
    "url": "https://example.com/audio.mp3",
    "format": "mp3",
    "codec": "raw",
    "rate": 16000,
    "bits": 16,
    "channel": 1
  },
  "request": {
    "model_name": "bigmodel",
    "enable_itn": true,
    "enable_punc": true,
    "enable_ddc": false,
    "show_utterances": true
  }
}
```

标准版限制：不超过 5 小时和 512 MB。格式支持 raw、wav、mp3、ogg、pcm、
spx、amr、aac、m4a。

### 本地 base64 兼容路径

旧版录音文件识别 API 曾正式记录通过 `audio.data` 上传文件二进制/base64。
新版 2.0 文档只展示 `audio.url`，但服务端仍为 `volc.seedasr.auc` 保留并支持：

```json
{
  "audio": {
    "data": "<base64>",
    "format": "mp3"
  }
}
```

这是“旧版文档有依据、2.0 服务继续兼容”的能力，不是新版文档当前明确列出的
输入形式。公网 URL 优先走 `audio.url`；本地文件使用该兼容路径。

## 常用参数

| 参数 | 说明 |
|---|---|
| `model_name` | 必填，固定 `bigmodel` |
| `enable_itn` | 数字、金额和日期书面化，默认 true |
| `enable_punc` | 自动标点，默认 true |
| `enable_ddc` | 语义顺滑；字幕保真建议 false |
| `show_utterances` | 返回分句、分词、时间戳和停顿信息；字幕必须 true |
| `enable_speaker_info` | 说话人分离，需同时开启 `show_utterances` |
| `ssd_version=200` | 不超过 5 人的非会议场景 |
| `ssd_version=300` | 长音频会议和声纹匹配场景 |
| `ssd_mode=0` | 200 模型普通模式，适合 3 分钟内 |
| `ssd_mode=1` | 200 模型聚类模式，适合 3 分钟以上非会议音频 |
| `enable_channel_split` | 双声道识别，通过 `channel_id` 标记 |
| `vad_segment` | true 为 VAD 分句，false 为语义分句 |
| `end_window_size` | 静音判停阈值 300–5000 ms，推荐 800–1000 |
| `enable_auto_lang` | 多语种自动检测；不能与 corpus 热词同时使用 |
| `enable_emotion_detection` | 返回分句情绪 |
| `enable_gender_detection` | 返回分句性别 |
| `show_speech_rate` | 返回分句语速 |
| `show_volume` | 返回分句音量 |

`corpus.context` 必须是序列化后的 JSON 字符串。热词总长度最多 5000 词；它们
用于提示模型，不保证强制命中。

Skill CLI 通过 `--context-json FILE` 接收未序列化的对象并完成序列化；
`--hotwords` 可作为快捷输入，和文件中的 `hotwords` 合并去重。官方限制
上下文最多 500 tokens，且不允许与 `enable_auto_lang` 同时使用。

说话人分离仅在 language 未指定或为 `zh-CN` 时生效。

## 查询与结果

查询请求体是空对象 `{}`，并把提交响应的 `task_id` 放在
`X-Api-Request-Id`。成功结果的时间单位为毫秒：

```json
{
  "audio_info": {"duration": 6312},
  "result": {
    "text": "整段文本",
    "utterances": [
      {
        "start_time": 480,
        "end_time": 5880,
        "text": "带标点的分句文本。",
        "additions": {"speaker": "1", "channel_id": "1"},
        "words": [
          {"text": "分", "start_time": 480, "end_time": 600, "confidence": 0}
        ]
      }
    ]
  }
}
```

## 状态码

| Code | 处理 |
|---|---|
| `20000000` | 成功 |
| `20000001` | 正在处理，继续查询 |
| `20000002` | 排队中，继续查询 |
| `20000003` | 静音，返回空转写 |
| `45000001` | 参数无效或重复请求，不重试 |
| `45000002` | 空音频，返回空转写 |
| `45000131` | 提交速率/时长额度限制，不重试 |
| `45000132` | 超过 512 MB，不重试 |
| `45000151` | 音频格式不正确，不重试 |
| `55000031` / `550xxxx` | 服务端临时错误，退避重试 |

排障时保留响应头中的 `X-Tt-Logid`。

## 官方文档

- 任务提交：https://docs.volcengine.com/docs/6561/2606791?lang=zh
- 结果查询：https://docs.volcengine.com/docs/6561/2606792?lang=zh
- 错误码：https://docs.volcengine.com/docs/6561/2611432?lang=zh

## 字幕时间轴约束

从视频抽音必须使用：

```text
-af aresample=async=1:first_pts=0
```

它会按源 PTS 填充 gap 或丢弃 overlap，避免长视频字幕累计漂移。
