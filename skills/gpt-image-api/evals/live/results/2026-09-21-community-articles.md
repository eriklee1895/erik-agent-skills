# GPT Image 2.5 community-article live check

Date: 2026-09-21

Sources:

- [赛博踱步：GPT Image 2.5 提示词、技巧、案例分享](https://mp.weixin.qq.com/s/9dy4JoyqZFHuAWO9utISpA)
- [远见明察：ChatGPT Images 2.5 的 6 种玩法](https://mp.weixin.qq.com/s/Dwbow-EPAmz1y640HJdLcg)

The posts supplied hypotheses only. They are community examples, not API contracts.
The run used the bundled CLI against the configured custom OpenAI Images endpoint with
explicit models and `quality=high`.

## Cases

| Case | Models | Result | Observation |
| --- | --- | --- | --- |
| Lamp move: one-line minimal delta vs structured `Change / Preserve / Avoid` | Flare, Sunburst | 4/4 accepted | Both moved the lamp and produced plausible local relighting; no clear visual winner for the longer prompt in this small sample. |
| Conservative low-resolution restoration | Sunburst | 1/1 accepted | A 512×341 derivative became clearer while the room remained recognizable; this is generative restoration, not lossless recovery. |
| 3×3 multi-camera continuity sheet | Flare, Sunburst | 2/2 accepted | Both kept the character, wardrobe, station, and shot logic coherent enough for a concept sheet. |
| 4×4 sixteen-pose action sheet | Flare, Sunburst | 2/2 accepted | Both produced ordered, visually consistent poses without a catastrophic identity collapse; frame-level anatomy QA remains required. |
| Visual abstract | Sunburst | 1/1 accepted | Supplied stages, implications, and readable labels rendered coherently without obvious extra copy. |
| Executive summary | Flare | 1/1 accepted | Supplied conclusion, evidence modules, and next actions rendered coherently without obvious extra copy. |

Total: 12 accepted outputs. The initial six-job batch had one transient connection failure;
the failed multi-camera Sunburst item succeeded when retried separately. API success and
visual acceptance are recorded separately.

## Decisions

- Add minimal-delta routing and explicit baseline-lock guidance; do not force a long
  preservation list when the edit target is singular and obvious.
- Add optional scaffolds for conservative restoration, multi-camera continuity sheets,
  and visual abstracts/executive summaries.
- Keep claims conditional. One live run does not prove lossless restoration, pixel locks,
  universal model superiority, or perfect frame/text consistency.
- Keep ChatGPT UI affordances such as `@Sketch`, Templates, Erase, and Remove Background
  as UI-to-API translations rather than inventing API parameters.

Outputs (ignored local artifacts):

```text
output/gpt-image-api/community-eval-20260921/
```
