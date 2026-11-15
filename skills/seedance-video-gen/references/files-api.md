# 文件管理 API 与 Seedance 输入的边界

按2026-11-15官方API核对。Files API用于上传、预处理、管理文件；Seedance视频生成API当前列出的来源是公网URL、data URL（仅图/音频）、asset://。**Files API返回的file-...不能直接写成asset://file-...，也没有文档化的file_id/file://输入方式。**

本skill没有Files CLI子命令；需要管理文件时按以下REST接口操作。不要因为提供了Files API文档，就把所有本地视频自动上传并宣称可直接作为生成输入。

| 操作 | 端点 | 关键规则 |
|---|---|---|
| 上传 | POST /files | multipart，file（二进制）与url二选一；purpose必填user_data或agent |
| 查询详情 | GET /files/{file_id} | search-files-api是按ID查详情，不是关键词搜索 |
| 列表 | GET /files | after游标、limit 1–100默认100、order asc/desc默认desc、purpose筛选 |
| 删除 | DELETE /files/{file_id} | 删除文件及存储内容；响应id/object/deleted；需确认不再被任务引用 |

所有端点基于 `https://ark.cn-beijing.volces.com/api/v3`，使用Bearer API Key。

```bash
# 上传：文件路径是Files API的输入，并不产生asset://素材
curl https://ark.cn-beijing.volces.com/api/v3/files \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -F 'purpose=user_data' -F 'file=@/absolute/path/reference.mp4'

curl https://ark.cn-beijing.volces.com/api/v3/files/file-xxx \
  -H "Authorization: Bearer $ARK_API_KEY"

curl 'https://ark.cn-beijing.volces.com/api/v3/files?limit=20&order=desc&purpose=user_data' \
  -H "Authorization: Bearer $ARK_API_KEY"
```

上传后状态可能为processing；应查询至active或failed。响应包括id、filename、purpose、created_at、expire_at、status；失败检查error。默认托管存储单文件≤512MB；显式tos存储视频可≤2GB、其他≤512MB，这些是**Files存储上限**，不改变Seedance视频参考≤200MB等限制。

`url`支持公网HTTP(S)或tos://；TOS URI需要tos.bucket与tos.prefix等存储配置和相应授权。Files的preprocess_configs.video是视频理解抽帧配置，不是Seedance生成参数，不填写Seedance Model ID来控制生成。

purpose=agent默认返回原文件download_url，24小时有效、最多下载100次。查询详情/列表返回已保存链接，**不会刷新有效期或次数**；链接有效期独立于expire_at。链接含临时访问凭证，避免公开或提交仓库。若尝试用download_url作Seedance公网URL，须确认服务端可访问、未过期且媒体规格满足Seedance限制；官方文档没有证明file ID可直接复用，不把这条桥接当默认工作流。

本地视频用于本skill的确定路径仍为：上传到可公开访问的对象存储URL，或使用平台已存在的asset://素材。素材库asset ID与Files文件ID是不同资源。

## 官方来源

- [上传文件](https://console.volcengine.com/ark/region:cn-beijing/docs/upload-files-api)
- [查询文件详情](https://console.volcengine.com/ark/region:cn-beijing/docs/search-files-api)
- [查询文件列表](https://console.volcengine.com/ark/region:cn-beijing/docs/list-files-api)
- [删除文件](https://console.volcengine.com/ark/region:cn-beijing/docs/delete-files-api)
- [视频生成输入来源](https://console.volcengine.com/ark/region:cn-beijing/docs/create-video-generation-task-api)
