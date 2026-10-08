# Model routing guide

Three curated models behind OpenRouter's dedicated Image API. Use this guide
for model tradeoffs; the paired prompting guides own model-specific controls,
reference handling, and verification limits.

## Decision matrix

| Job | Choose | Reason |
|---|---|---|
| Final image with strict copy, hierarchy, counts, or edits | **sunburst** | precision-oriented GPT Image 2.5 tier |
| Fast everyday image, draft, exploration | **flare** | speed-oriented GPT Image 2.5 tier |
| Multiple candidates per call | **sunburst / flare** | `--n` up to 10; banana gives 1 |
| Routine subject/product recontextualization | **banana** | useful reference editing at 1K/2K; inspect face, shape and copy |
| Same job with especially strict identity/label preservation | **sunburst** | prefer precision, inspect the preserved details |
| Ultra-wide/ultra-tall: `8:1`, `1:8`, `4:1` | **banana** | supported ratios; 2.1 addresses panoramic tiling artifacts |
| Canvas beyond GPT Image 2.5's documented pixel/edge limits | **banana** | 4K outputs can exceed those limits; inspect actual detail and dimensions |
| Transparent asset | **sunburst / flare** | explicit transparent-background support |
| Generate from current verified facts | research, then chosen model | this CLI does not activate Google Search grounding |

Model reference limits alone do not rank fusion quality: GPT accepts 16 images,
banana 14. Use the fewest references that explain the job, with an explicit role
and source of authority for each. Improved text rendering makes banana worth
trying for posters; it does not guarantee every glyph or layout constraint.

Banana's clearest format advantage is extreme ratios: GPT Image 2.5's documented
API range is 1:3 to 3:1, with each edge at most 3840 pixels and at most 8,294,400
pixels total. Our Banana 4K / 21:9 probe returned 6336×2688. This establishes a
larger output canvas, not superior visual detail or native rendering. The CLI
does not expose GPT's custom `size` control.

## Sunburst vs Flare

Both have identical parameter choices and per-token pricing. Flare is the
small/speed model; Sunburst is the base/quality model. The existing 2026-09-30
skill probes at `quality high` measured medians of $0.042/34s for Sunburst and
$0.042/18s for Flare (1372 image tokens). Those are historical samples, not
current latency or equal-cost guarantees. Compare actual `usage.cost` because
token consumption can differ even at the same quality label.

Choose Flare when fast iteration matters, Sunburst when precise final edits
matter. Model selection and `--quality` are separate controls; try higher quality
only when it addresses a visible unmet requirement.

## Banana — Nano Banana 2.1

Choose `banana` for wide/panoramic formats or routine reference-based
recontextualization. Start at `1K` for drafts or large poster headings, `2K` for
finer copy/detail, and `4K` when the deliverable needs more pixels.
For strict identity or label preservation,
compare with Sunburst. See [banana-prompting.md](banana-prompting.md) for the
parameter matrix, source authority, follow-up edits, and access-path limits.

Google's current standard image-output estimates are $0.0336 (1K), $0.0504 (2K),
and $0.1134 (4K). OpenRouter's checked endpoint publishes $30 per million image
output tokens. Read the actual response usage; estimates exclude input,
text/thinking, and other applicable charges. 1K/2K output is about half the old
Nano Banana 2 price; 4K is about 25% lower. Output dimensions and tokens do not
establish whether detail was rendered natively or upscaled. The inspected local
probes and measured per-call tradeoffs are summarized in
[banana-prompting.md](banana-prompting.md).

## Evidence boundaries

2.1's main upgrades are better editing/subject consistency, text/layout, and
panoramic artifact handling. 4K, multiple references, and Google Search grounding
were already available in Nano Banana 2. The underlying Google API's integrated
Web/Image Search can simplify a factual-image workflow, but this CLI route does
not activate it. GPT workflows can also search before generating; grounding
support alone does not establish better factual accuracy.

Google's model card reports improvements over Nano Banana 2 in text-to-image,
editing, multi-character consistency, and mask/ink editing. Arena's 2026-10-07
text-to-image and 2026-10-06 single-image-edit snapshots still place 2.1 behind
GPT Image 2.5 Sunburst/Flare and GPT Image 2. Overall preference does not settle
a particular prompt; inspect the result for the actual brief. The 12-call local
Banana probe did not compare matched GPT outputs, so it cannot establish better
Chinese text, multi-reference fidelity, speed, or cost than Flare/Sunburst.
In particular, GPT quality levels change cost; Banana is not universally cheaper.

## Prompting references

- [sunburst-flare-prompting.md](sunburst-flare-prompting.md): exact copy,
  Change/Preserve edits, references, variants, transparency.
- [banana-prompting.md](banana-prompting.md): text/layout, reference authority,
  stateless follow-ups, extreme-ratio composition, endpoint boundaries.

## Access path and errors

This skill uses OpenRouter for GPT Image 2.5 Sunburst/Flare and Nano Banana 2.1.
It does not need another image skill. A capability available through Google's
native API or a chat route is not automatically available through `/images`.

402: credits/account issue; 404: model or provider unavailable; 429: inspect
whether it is transient throttling or exhausted upstream quota; 502: upstream
failure. Do not promise that every failed request is unbilled; inspect available
usage/account evidence. The CLI does not retry or switch models automatically.

## Official sources

- [OpenRouter Image API](https://openrouter.ai/docs/guides/overview/multimodal/image-generation)
- [Nano Banana 2.1 on OpenRouter](https://openrouter.ai/google/gemini-nano-banana-2.1)
- [Google model card](https://deepmind.google/models/model-cards/nano-banana-2-1/)
- [Google image-output pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [OpenAI GPT Image guidance](https://developers.openai.com/api/docs/guides/image-prompting)
- [OpenAI output size/format limits](https://developers.openai.com/api/docs/guides/image-generation)
- [Arena text-to-image](https://arena.ai/leaderboard/text-to-image) and
  [single-image editing](https://arena.ai/leaderboard/image-edit)
