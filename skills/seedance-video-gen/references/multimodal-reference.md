# Seedance 2.5 系列多模态参考

标准版与flash共用role与任务锁定规则；数量按模型校验。详见[官方创建API](https://console.volcengine.com/ark/region:cn-beijing/docs/create-video-generation-task-api)与[提示词指南](https://console.volcengine.com/ark/region:cn-beijing/docs/seedance-2-5-prompt-guide)，核对日期2026-11-15。

## 容量与格式

| 素材 | 标准版 | flash | 格式与体积 |
|---|---|---|---|
| 图片 | ≤30 | ≤10 | JPEG/PNG/WebP/BMP/TIFF/GIF/HEIC/HEIF；单张<30MB |
| 视频 | ≤10 | ≤5 | MP4/MOV；单段≤200MB |
| 音频 | ≤10 | ≤5 | WAV/MP3；单段≤15MB |

图像宽高各300–6000px，宽高比[0.4,2.5]。视频同宽高/宽高比，24–60fps，总像素407696–8295044；H.264/AVC或H.265/HEVC视频，MP4音轨AAC/MP3，MOV另允许PCM。

视频每段2–30秒（待编辑视频4–30秒），总时长≤30秒；音频每段2–30秒，总时长≤30秒。参考视频可到4K，但**输出**仍服从模型上限。30/10/10与10/5/5是输入条数限制，不是推荐堆满数量。

## 传输方式

- 图片：公网URL、base64 data URL、asset://；本地图片CLI自动编码并校验尺寸/体积。
- 音频：公网URL、base64 data URL、asset://；本地音频CLI自动编码。
- 视频：**仅公网URL或asset://**，本地路径与base64均不支持。
- 请求体≤64MB，CLI留余量以60MB拦截；大图/音频改公网URL。API会校验远程媒体规格。
- Files的file-...不是asset://；本地视频可先上传公网对象存储。不要自动拼接file://或asset://file-...，见 [files-api.md](files-api.md)。

## 模式与content

```json
[
  {"type": "text", "text": "图片1是角色外观，视频1只参考动作，音频1只参考音色。"},
  {"type": "image_url", "image_url": {"url": "https://example.com/character.png"}, "role": "reference_image"},
  {"type": "video_url", "video_url": {"url": "https://example.com/motion.mov"}, "role": "reference_video"},
  {"type": "audio_url", "audio_url": {"url": "https://example.com/voice.wav"}, "role": "reference_audio"}
]
```

**按各自类型的上传顺序编号**；图片1与视频1各是该类第一个素材。绑定写在prompt里，不能只在图上写角色名字。

| 模式 | 组合与约束 |
|---|---|
| 文生 | text |
| 首帧 | 一张first_frame；ratio=adaptive |
| 首尾帧 | 一张first_frame+一张last_frame；ratio=adaptive；画幅建议一致 |
| 多模态参考 | reference_image/video/audio自由组合，包括仅音频；ratio/duration可指定 |
| 编辑 | 至少一段reference_video；edit + ratio=adaptive + duration=-1 |
| 延长 | 至少一段reference_video；extend + ratio=adaptive；duration为成片总长 |

首帧/首尾帧不能与reference_*混用；仅传last_frame无效。想同时借助其他参考并近似指定首帧，可全用reference_*并写「图片1为首帧」，但这种参考任务不严格锁定图像/画幅。

## 参考如何分工

| 用途 | 写法 |
|---|---|
| 外观/身份 | 图片1是角色外观参考，全片用同一角色名 |
| 服装/道具 | 图片2只参考服装/材质，不改变角色身份 |
| 动作/运镜 | 视频1只参考动作，视频2只参考镜头运动 |
| 音色 | 图片1角色使用音频1的音色；明确说话人 |
| 配乐/节奏 | 音频1参考音乐情绪与节拍，不要求原轨逐字节粘贴 |
| 风格/光影 | 只参考图片3的侧光与色调 |
| 关键帧 | 以图片1至图片N顺序作为关键帧，动作在相邻图之间衔接 |

白模提供构图/动势，目标材质另写；宫格提供剧情参考，不保证逐格复现。减少互相冲突、重复的参考。建议每个需稳定的元素有明确来源，不能机械规定一个元素只能有一份素材。

官方稳定性建议：主体音/视频1–5个主体、单段5–10秒，图片1–8个主体，编辑附图1–5张、源片≤20秒；宫格少于15格且少写文字。更大输入可能需要迭代，先服从flash10/5/5硬上限。

## 编辑与延长

编辑写具体A→B，必要时限定秒数和保留范围；如有多段视频，写清编辑哪段。API类型引导不代替prompt意图。延长写前/后方向和边界接续动作，源片5秒续7秒需duration=12。MOV进出有助于声画一致性，成片仍需实际检查。

两段成片补衔接时，将两段作为reference_video，写清视频1结尾到视频2开头的转场，可用auto/adaptive/-1。检查总时长与动作连续性，不保证所有场景自动无缝。

## 人像与信任产物

不直接上传含真人人脸的图/视频；使用平台允许的预置虚拟人像或已授权素材asset://，或按官方规则使用同账号近30天内的原始模型信任产物。Files上传不会自动赋予素材人像授权，也不会生成asset ID。
