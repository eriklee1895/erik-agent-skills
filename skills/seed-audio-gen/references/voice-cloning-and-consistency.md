# Voice Cloning and Character Consistency Guide

Use this guide when a Seed Audio task needs reusable character voices,
multi-character continuity across segments or episodes, or QA under emotional
acting and dense SFX/BGM.

For API flags and `@音频N` syntax, use `SKILL.md` and
`seedaudio-prompt-guide.md`. This guide covers production decisions rather than
repeating the CLI reference.

## Core principle

Maintain **one identity master per character**. Keep identity traits stable and
direct emotion per scene. Do not create a separate master for every emotion by
default.

## Choose the voice source

| Need | Recommended source | Trade-off |
|---|---|---|
| One-off flexible character | Describe the voice in the prompt | Fast, but not a durable identity by itself |
| Known catalog voice | `--speaker <id>` | Easy reuse; less unique |
| Reusable custom character | Clean `--ref-audio` master | Best fit for 2–3 custom roles in one scene |
| Long-running fixed cast | Registered `_tob` ICL voice when available | Operational setup and voice-slot billing |

A prompt-designed voice becomes reusable only after generating candidates,
selecting one output, and freezing a clean excerpt as its identity master.

## Build an identity master

### 1. Design voice DNA

Define only traits that should remain recognizable across scenes:

- age band and pitch center;
- resonance placement, such as chest, throat, or forward oral resonance;
- texture, such as clear, dry, breathy, or lightly rough;
- articulation, accent, and habitual rhythm;
- one or two distinguishing traits relative to the rest of the cast.

Separate these from acting directions:

| Identity: keep stable | Performance: vary per line or scene |
|---|---|
| pitch center | temporary pitch movement |
| resonance placement | loudness and projection |
| texture and age impression | anger, grief, fear, warmth |
| accent and articulation identity | pace, pauses, breath, emphasis |

Make main characters differ on at least two audible dimensions. Three similar
low male voices can remain technically cloned yet still be hard to distinguish
in a mix.

### 2. Generate or collect auditions

Create 3–5 candidates per role before formal production. Each candidate should
normally be:

- one speaker only;
- about 15–25 seconds and within the API's 30-second / 10MB limit;
- dry or nearly dry, without BGM, SFX, other voices, or strong reverb;
- natural, neutral dramatic speech with several phonetic and sentence shapes;
- free of forced long timestamp windows that turn slow pacing into part of the
  reference identity.

An audition prompt can use this shape:

```text
录音棚单人干声，无音乐、无环境音、无混响。
角色是一位四十多岁的男性：中低音、自然胸腔共鸣、轻微干燥颗粒感，
思考时短暂停顿，但保持自然对话语速。不要现代播音腔，不要故意压嗓。
请连续说三句：一句平静判断，一句低声提醒，一句坚定承诺。
```

Requested duration is not guaranteed when the text finishes naturally. Record
the actual duration instead of stretching a master solely to hit a target.

### 3. Select and freeze

Listen to the candidates in context, choose one, and freeze:

- the original audio file;
- a stable semantic filename such as `cast/role_master.wav`;
- character name and voice-DNA description;
- fixed `@音频N` binding when the cast shares scenes.

WAV is recommended for a long-lived editable master because it avoids repeated
lossy encoding. It is not an API requirement: WAV, MP3, PCM, and OGG Opus are
supported. Converting an already compressed MP3 to WAV does not restore lost
detail. Clean stereo is acceptable; mono can be convenient for voice-only
editing.

## Bind a multi-character cast

Seed Audio accepts at most three reference audios per call. Their CLI order is
the binding contract:

```text
@音频1 -> cast/lead_master.wav
@音频2 -> cast/partner_master.wav
@音频3 -> cast/mentor_master.wav
```

Keep the same source files, order, and mapping in every segment. Repeat the
character list in each prompt and bind the token at each speaker's line when a
scene is complex.

```bash
uv run scripts/seed-audio-gen.py "$PROMPT" \
  --ref-audio cast/lead_master.wav \
  --ref-audio cast/partner_master.wav \
  --ref-audio cast/mentor_master.wav \
  --format wav \
  --sample-rate 48000 \
  --subtitle \
  --output-dir renders/segment-01
```

For more than three fixed characters:

- pass only the active cast when no more than three speak in that scene, while
  reusing each role's original master whenever the role returns;
- or generate characters separately and mix them downstream when four or more
  identities must remain independently controlled;
- consider registered fixed voices for a recurring large cast.

## Direct acting without replacing identity

Keep the identity clause unchanged and append scene-specific performance:

```text
@音频1保持原有年龄感、中低音重心、胸腔共鸣和干燥质地。
本句表演：压低音量、增加少量气声，用近距离耳语说完；不要改变基础声线。
```

Whisper, crying, and shouting can mask identity cues. Treat them as QA hotspots,
not automatic failures or prohibited states.

Default production response to an ambiguous critical line:

1. Keep the same identity master.
2. Tighten the performance direction without redefining voice DNA.
3. Generate 2–3 candidates for that line or scene.
4. Select by listening in the real mix.

Create a state-specific reference only after the same critical state repeatedly
fails and the added reference can fit the three-slot limit. Do not maintain a
full emotion-master matrix for ordinary production.

## Long-form and episodic production

For multi-character work longer than 120 seconds:

1. Split into narrative units that can be regenerated independently; 60–100
   seconds is often practical, but story and dialogue density decide the size.
2. Generate serially for the first production pass and listen before continuing.
3. Reuse the clean per-character masters and identical binding order in every
   segment.
4. Preserve prompt, result JSON, `.meta.json`, `log_id`, `attempts`, duration,
   and cost.
5. Design segment boundaries around room tone, ambience, or music handles, then
   assemble and crossfade downstream.

For a single-speaker extension, using a clean tail no longer than 30 seconds as
the next reference can help continuity. For multi-character scenes, do not use
a finished mix containing multiple voices, SFX, and BGM as a character identity
reference. Keep the original solo masters as the identity source.

Batch mode is useful only when every item carries the intended references and
binding order. Top-level `--ref-audio` flags are not shared into batch items.

## Production QA versus research evaluation

### Ordinary production

Use proportional checks:

- audition and approve each identity master;
- test a short scene containing all active characters;
- listen to every formal segment for identity, acting, intelligibility, SFX,
  BGM balance, and transitions;
- spot-check whisper, crying, shouting, telephone effects, and distance effects;
- rerender only ambiguous or failed segments.

Use `--subtitle` to help check lines and timing, but do not rely on it alone.
Complex mixed scenes can return `subtitle: null`; listening remains the gate.

### Research or regression testing

Blind listening, multiple listeners, randomized filenames, or speaker
embeddings can quantify a model or workflow. They are optional research tools,
not universal production requirements. Set thresholds for that experiment and
do not turn one stress-test miss into a blanket ban.

Always score identity consistency separately from emotion accuracy. A line can
sound like the same person while underplaying anger, grief, or shouting.

## Quick reference

| Situation | Default action |
|---|---|
| Need a unique reusable voice | Generate several dry neutral auditions; freeze one master |
| Three roles in one scene | Same three masters and same `@音频N` order every call |
| Ten-minute drama | Independent serial segments using original solo masters |
| Prior segment includes voices + SFX + BGM | Do not use it as a character identity reference |
| Whisper/shout sounds ambiguous | Keep master; tighten direction; render 2–3 candidates |
| Exact text required | Request verbatim delivery and verify; use TTS if accuracy is hard |
| Subtitle is null | Perform listening QA and retain `log_id`/metadata |
| Four-plus controlled voices | Rotate active cast or generate/mix separately |

## Common mistakes

- Freezing the first generated voice without auditioning alternatives.
- Using a slow, highly emotional, noisy, or reverberant clip as the only master.
- Changing reference order between segments.
- Feeding a multi-speaker finished mix back as one character's identity.
- Maintaining separate masters for every emotion before a real failure exists.
- Treating requested duration as guaranteed output duration.
- Treating subtitle or embedding scores as a substitute for listening.
- Applying research thresholds as universal production gates.
