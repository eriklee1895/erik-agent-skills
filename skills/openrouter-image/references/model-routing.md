# Model routing guide

Three curated models behind one OpenRouter image API. The guidance here is
grounded in ~75 real paid calls run on 2026-09-30 (our own matrix plus a
cross-model probe), not just vendor marketing.

## Decision matrix

| If the job is… | Choose | Why |
|---|---|---|
| Final deliverable; must be *exactly* as specified | **sunburst** | highest precision for text, layout, edits |
| Many verbatim labels / dense infographic / slide | **sunburst** | most reliable typography & hierarchy |
| Precise count or numbering | **sunburst** | follows structural constraints closest |
| Multi-image edit where nothing may drift | **sunburst** | best subject/region preservation |
| Fast everyday image, draft, exploration | **flare** | speed tier, identical parameter matrix |
| Batch of variants of one prompt (`--n`) | **sunburst / flare** | up to 10 per call; banana gives 1 |
| Fuse many reference photos / products | **banana** | strongest multi-reference fusion (14) |
| Conversational edit of an existing image | **banana** | plain-language change, rest preserved |
| Ultra-wide / ultra-tall (8:1, 21:9), native 4K | **banana** | extreme formats + genuinely native 4K |

## sunburst vs flare — same family, same price, different speed

Both are GPT Image 2.5 with identical parameters and **identical per-token
pricing**; flare is the *small/speed* model, sunburst is the *base/quality*
model. Measured directly:

| quality high, real work | cost median | latency median | image tokens |
|---|---|---|---|
| sunburst | $0.042 | **34s** | 1372 |
| flare | $0.042 | **18s** | 1372 |

So the common mental model "flare = cheaper" is wrong — **flare saves time, not
money**. To spend less, lower `--quality`, not the model. Flare's quality is
described by OpenAI as "comparable to GPT Image 2"; sunburst beats it, and the
gap widens with task difficulty (blind-arena deltas vs the previous gen: text-
to-image sunburst +40 / flare +18; multi-image edit +81 / +47). Use flare to
find the direction, sunburst to finish.

Two separate levers: model (`flare`) picks the fast family; `--quality max`
raises per-request reasoning. "flare + quality max" is the fast family at
maximum detail.

## banana — Nano Banana 2

`google/gemini-3.1-flash-image`. Note this is *not* `gemini-3-pro-image`
(Nano Banana Pro) — 3.1 Flash is the newer release that reaches Pro quality at
flash speed.

- Detail lever is `--resolution` (512/1K/2K/4K), not quality.
- Returns exactly **one** image; n>1 impossible.
- Up to **14** reference images; native extreme ratios (8:1, 4:1, 21:9).
- **No transparency** and no streaming on the dedicated images endpoint.

Cost is per resolution tier, regardless of ratio:

| request | native returned | cost | image tokens |
|---|---|---|---|
| 1K, 1:1 | 1024×1024 | $0.067 | 1120 |
| 2K, 16:9 | 2752×1536 | $0.101 | 1680 |
| 2K, **8:1** | **5856×704** | $0.101 | 1680 |
| 4K, 21:9 | **6336×2688** | $0.151 | 2520 |

The 4K / ultra-wide pixels are genuinely native (tokens scale 1120→1680→2520),
not upscaled.

## Output "personality" — observed directly

All three produce top-tier results; the difference is behavior, not a quality
ranking:

- **sunburst** is the most literal — it keeps the framing, product shape, and
  scope you specify. Best when you need a lock.
- **flare** sometimes invents text you never asked for (in one portrait it
  designed an entire magazine cover, "INSPIRE / 设计让生活更美好"). Watch for
  unwanted added copy.
- **banana** is the most creatively liberal — it may change a half-turn into a
  wide standing shot, or a round watch into a square one. Great when you want
  ideas; risky when the composition/product form is fixed.

## Variance warning (important)

Across two independent test batches on the same day, banana's Chinese-text
result was inconsistent: our matrix rendered every fixed string flawlessly,
while a parallel cross-model probe produced a duplicated phrase
("时代时代") and, on a 国风 image, stray gibberish small text. Nano Banana 2
has **real per-call output variance**. Do not certify it from a single good
result — for production work, generate, inspect, and rerun on failure. The GPT
models were stable across the same tests.

## Chinese / bilingual text

The fixed-copy posters (dense Chinese + bilingual English) came back with zero
wrong characters from all three in our matrix. Chinese typography is no longer
a reason to pick between these flagships — choose by style, edit needs, and
format. (When the same prompt was run across more models elsewhere, Nano
Banana Pro and the original Nano Banana failed; that variance is why the
shortlist uses 3.1 Flash specifically.)

## Failure modes

- **banana, transparency / n>1**: impossible by design — the CLI rejects
  rather than pretending.
- **mask edits are not perfectly deterministic even on good gateways**: over
  two rounds the same mask request against one upstream once flattened the
  transparent region to black (reproduced via the official SDK), then
  succeeded. Retry critical mask edits; don't treat one black-box result as
  the model's fixed behavior.
- **SSE can silently downgrade**: a `stream:true` request returns plain
  buffered JSON when no partial frame is produced (low quality / simple scene).
  Clients must parse by response content-type, not assume an SSE stream.

## Prompting craft

These are strong models; write a clear natural-language brief rather than
filling in rigid templates — templates tend to flatten the output. The
model-specific facts that are *not* obvious live in the paired references:

- [sunburst-flare-prompting.md](sunburst-flare-prompting.md) — text allowlists,
  Change/Preserve edits, references, variants, transparency.
- [banana-prompting.md](banana-prompting.md) — many-reference fusion,
  conversational edit style, extreme-ratio composition.

## Access path, not capability

This is an **access-path** split, not a capability split. GPT Image and Banana
also render 国风 / Chinese commercial looks and Chinese text very well. Other
image models a user may already access through a different provider are simply
not duplicated here — no need to pay for the same model through two gateways.

| This skill's access path | Models |
|---|---|
| OpenRouter | GPT Image 2.5 Sunburst/Flare, Gemini 3.1 Flash |

## Evidence

- Our 45-call matrix: `output/skill-research/live-findings.md` + `live/matrix.json`
- Full API reference field test: `research/01-openrouter-images-api.md`
- GPT 2.5 official/arena data: `research/03-gpt-image-2.5.md`
- 16-model cross probe (variance data): `research/04-landscape.md`

## Links

- Per-model docs: `https://openrouter.ai/<id>` · Keys: https://openrouter.ai/keys
- Errors: 402 out of credit · 404 unknown model/no provider · 429 upstream
  rate limit · 502 upstream failure (not billed)
