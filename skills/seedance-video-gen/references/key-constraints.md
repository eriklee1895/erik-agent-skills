# Seedance 2.5 系列关键约束

核对日期2026-11-15。先看[模型矩阵](seedance-2.5.md)，执行参数以[API参考](api-reference.md)为准。

## 模型与任务

- 默认标准版；仅用户明确要求flash时切换，低成本/批量不是切换依据。
- 两款均4–30秒或-1；标准版480p/720p/1080p，flash480p/720p；均无4K输出。
- 标准版参考数量≤30图/10视频/10音频；flash≤10图/5视频/5音频。
- 首帧/首尾帧必须ratio=adaptive；编辑必须adaptive与duration=-1；延长必须adaptive，duration是成片总长。
- 首帧/首尾帧与reference_*互斥；单独尾帧无效。
- Draft仅标准版，480p样片→同模型1080p；flash不支持Draft或凭普通任务ID升版。
- 无frames/seed/camera_fixed入参，无flex服务等级。

## 输入媒体

| 类型 | 限制 | 传输 |
|---|---|---|
| 图片 | 单张<30MB；宽高各300–6000px；宽高比[0.4,2.5]；JPEG/PNG/WebP/BMP/TIFF/GIF/HEIC/HEIF | URL/base64/asset:// |
| 视频 | 单段≤200MB；MP4/MOV；24–60fps；宽高各300–6000px；宽高比[0.4,2.5]；总像素407696–8295044 | 仅URL/asset:// |
| 音频 | 单段≤15MB；WAV/MP3 | URL/base64/asset:// |
| 请求体 | 官方≤64MB；脚本以60MB留JSON余量 | 大素材优先公网URL |

视频单段2–30秒，编辑待编辑片4–30秒，所有视频合计≤30秒。音频单段2–30秒、所有音频合计≤30秒。二者各算总时长；不能仅检查条数。

脚本前置校验模型、输出规格、参考数量、角色组合、本地图片像素与体积；远程素材和音视频时长/编码仍由API校验，提交前有元数据时先核对。Files API存储上限不等于生成输入上限；file ID不等于asset ID，见 [files-api.md](files-api.md)。

## 音频与语言

两款均支持仅音频参考。generate_audio默认true，输出为**双声道**；false无声。参考音频用于条件引导，会重做输出音轨，不是原样贴轨；音色/节拍/口型都需检查实际成片。

支持中、英、西班牙、印尼、葡萄牙、日、马来、泰、阿拉伯、越南、韩语。中文建议≤500字、英文≤1000词；对白用引号并写明说话人和语种。支持「不要字幕」「无bgm，只保留环境音」等文本控制，完全静音用API开关。

## 素材稳定性建议（不是硬上限）

官方提示词指南建议主体音/视频1–5个主体、单段5–10秒；主体图1–8个主体；编辑附带参考图1–5张、待编辑视频≤20秒更稳；宫格少于15格，简约线稿优先。更多主体或更长片可能降低稳定性，仍不能超过所选模型硬限制。flash最多10张图，不可套用12张图的探索建议。

超过5主体时优先单视图；需多视角可拆成不同图片，少用多视角拼图。素材绑定到外观、动作、运镜、音色等具体用途；参考足够清楚时少重复描述。

## 联网搜索与配额

web_search仅纯文本，一个text，不能和任何媒体输入混用；模型自主选择调用次数，可能0次，增加等待时间。需要结合网上信息与素材时，可先独立查证信息并整理到prompt，再提交多模态生成。

提交与running并发是不同配额；以当前账号、Endpoint、模型配额为准。不要继承旧模型历史压测的「无限流」「共享20槽」结论。脚本对429及暂时服务错误退避；批量付费并发压测需明确请求，不属于默认生成步骤。

普通轮询默认20秒；查询速率遵循当前平台配额，不用列表端点逐个任务轮询。

## 留存与交付

- Draft：2026-10-28 10:00（UTC+8）起创建的ID有效14天，之前7天；其他任务ID7天。
- 成片URL24小时、最多下载100次，及时下载/转存；尾帧JPEG。
- 本地轮询超时不会取消服务端任务；保留task ID后继续poll，避免重复提交。
- running任务不能取消；queued可取消，其他终态可删除记录，包括cancelled。
- 真人人脸图/视频不直接上传；按官方允许的预置虚拟人像、已授权素材、同账号近30天原始信任产物规则使用。不要把普通本地人像声明为已授权asset。

## 官方来源

[创建任务API](https://console.volcengine.com/ark/region:cn-beijing/docs/create-video-generation-task-api)、[系列教程](https://console.volcengine.com/ark/region:cn-beijing/docs/seedance-2-5)、[系列提示词指南](https://console.volcengine.com/ark/region:cn-beijing/docs/seedance-2-5-prompt-guide)、[查询任务](https://console.volcengine.com/ark/region:cn-beijing/docs/get-video-generation-task-api)。
