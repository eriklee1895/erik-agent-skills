# 豆包搜索 — 故障排查与凭证配置

## 获取与配置 API Key

入口：<https://console.volcengine.com/search-infinity/api-key>

| Key 类型 | 创建位置 | 能调用的版本 |
|---|---|---|
| 按量后付费 Key | API Key 管理 →「按量后付费」标签页 | Custom 版 + Global 版（web/image/visual 全部） |
| 订阅套餐 Key（包月） | API Key 管理 →「订阅套餐」标签页 | **仅 Custom 版** web / image；调 Global 报 10409 |

> 两种 Key **相互隔离**，拿错 Key 是最常见的鉴权问题。每月 500 次免费额度两版共享。

脚本按以下顺序找 Key：`--api-key` 参数 → `VOLC_WEB_SEARCH_API_KEY` → `WEB_SEARCH_API_KEY` → `ASK_ECHO_SEARCH_INFINITY_API_KEY` → skill 目录 `.env` → 当前工作目录 `.env`。

开通服务：<https://console.volcengine.com/search-infinity/web-search>（每月免费 500 次；超额后按量 0.02 元/次，或购买包月套餐）。

## 错误码

### Custom 版（/search_api/web_search）

| 错误码 | 含义 | 处理 |
|---|---|---|
| `invalid_api_key` / `10403` | Key 无效、未开通服务或 Key 类型不匹配 | 确认 Key 来自豆包搜索控制台（不是火山方舟 Ark）；已开通服务；套餐 Key 不要用于 Global |
| `10400` | 参数错误 | 检查 Query 是否为空、字段类型；Filter 参数需嵌套在 `Filter` 对象内 |
| `10401` | TOP 网关 Token 无效 | AK/SK 接入时检查 Token（本 skill 脚本只用 API Key，一般不涉及） |
| `10402` | 搜索类型非法/未开通 | `--type` 只能是 web/image/visual；确认控制台已开通对应类型 |
| `10406` | 免费额度用尽 | 开通按量后付费或购买套餐 |
| `10407` | 无可用免费策略 | 检查账户状态或联系支持 |
| `10408` | 服务未付费开通 / 欠费 | 控制台开通或充值；欠费 24h 内充值可恢复 |
| `10409` | 套餐模式不支持当前搜索类型 | 订阅套餐 Key 不能调 Global（global_search），换按量后付费 Key |
| `10410` | 无可用订阅套餐 | 套餐未开通/已到期，检查控制台套餐状态 |
| `10412` | 套餐额度不足 | 升配套餐或换按量后付费 Key |
| `10500` | 服务内部错误 | 等几秒重试；持续失败带 RequestId 联系支持 |
| `700429` | 超过 QPS 限流（默认 10 QPS） | 降频重试；批量调用加 `--queue` 排队；需要更高配额可提工单 |
| `100013` | 子账号未授权 | 主账号为子账号添加 `TorchlightApiFullAccess` 权限 |

### Global 版（/search_api/global_search）

Global 版错误可能出现在两处：`ResponseMetadata.Error.Code`（HTTP 层）或 `Result.ErrorCode`（业务层，0 为成功）。

| 错误码 | 含义 | 处理 |
|---|---|---|
| `700901` / `invalid_api_key` | APIKey 无效 | 检查 `Authorization: Bearer <KEY>`；Key 必须是**按量后付费**类型 |
| `10400` | 参数错误 | 文搜检查 Query；图搜图检查 `ImageQuery`（Url/ImageBase64 二选一，base64 不带 `data:` 前缀）；字段类型 |
| `10403` | 账号或权限错误 | 检查 Key、账号信息与服务开通状态 |
| `10408` | 服务未付费开通 / 欠费 | 控制台开通/充值 |
| `10409` | 套餐模式不支持 | Global 仅支持按量后付费，不支持订阅套餐 Key |
| `10410` / `10412` | 无可用套餐 / 额度不足 | 检查账号开通状态与额度 |
| `10500` | 内部错误 | 重试；持续失败带 RequestId 排查 |
| `10501` | 免费额度链路依赖失败 | 重试；持续失败带 RequestId 排查 |
| `700429` | 请求频率超限 | 降频重试或加 `--queue` |
| HTTP 500 `engine intervene empty` | 过滤条件互相矛盾导致空召回（例如 `site:github.com` 同时加 `--icp-host-only`） | 去掉矛盾条件后重试 |

## 结果质量问题

| 现象 | 处理 |
|---|---|
| 结果太少/没有 | 精简 query 只留核心实体词；去掉 `--authoritative-only`/`--industry`（会过滤掉如意结果并减少召回）；`--count` 调大 |
| 口语长句召回差 | Custom 加 `--query-rewrite` 让服务端改写 query |
| 不够新 | 用 Custom `--time-range day/week` 等可靠参数过滤；Global 版官方列出支持 query 内高级语法做时效限制但未公开语法，不稳定时退回 Custom |
| 不够权威 | `--authoritative-only`（仅非常权威）或 `--industry gov`（政府/央媒/国家机构，权威子集更严格） |
| 海外内容太少 | 换 `--global`；Global 摘要长度用 `--max-snippet-length` 调大（≤3000，推荐 ≤1000） |
| Global 结果太杂/想要国内源 | 加 `--icp-host-only`，或 query 里用 `site:域名` 高级语法（实测有效；官方还列出屏蔽域名/时效限制的高级语法但未公开格式） |
| 图片分辨率低/方向不对 | `--min-short-edge 1080`、`--orientation landscape/portrait/square` |
| 想要网页全文 | Custom 的 `Content` 默认返回，`--content-format markdown` 可切 markdown；`--need-content` 是「仅保留有正文的结果」的过滤、不是正文开关；Global 不返回正文 |

## 官方文档

- 产品简介（版本差异）：<https://www.volcengine.com/docs/87772/2272949>
- 新功能发布记录：<https://www.volcengine.com/docs/87772/2272950>
- 站点权威度分级说明：<https://www.volcengine.com/docs/87772/2518319>
- 产品计费：<https://www.volcengine.com/docs/87772/2272951>
- Custom 版 API 参考：<https://www.volcengine.com/docs/87772/2272953>
- Global 版 API 参考：<https://www.volcengine.com/docs/87772/2548026>
- AI 工具（MCP/Skill）接入指南：<https://www.volcengine.com/docs/87772/2297384>
