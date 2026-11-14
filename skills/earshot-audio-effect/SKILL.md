---
name: earshot-audio-effect
description: Generate and customize procedural sound effects for videos and animations with Earshot on CPU. Use for clicks, pops, switches, whooshes, impacts, chimes, keyboard sounds, coherent sound kits, and custom DSP recipes (音效、转场声、提示音、自定义音效). Suitable for HyperFrames or other video engines that consume WAV files. Speech, BGM, audio understanding, and model-scored sound search belong to other tools.
---

# Earshot Audio Effects

Produce project-local PCM WAV files and measured sync points. Use tuned bank
sounds first, adjust supported knobs when close, and write a project recipe when
the structure needs to change. No audio-model calls, Torch, or Transformers.

## Runtime and entry point

Set `SKILL_DIR` to the installed directory containing this `SKILL.md`. Run the
bundled script with `uv`; do not install upstream Earshot separately:

```bash
uv run --locked --script "$SKILL_DIR/scripts/earshot_sfx.py" doctor
```

Requires `uv` **0.12.5 or newer** and Git. uv prepares Python 3.11–3.14 and the
script environment. First use needs network for source and dependencies; warmed
caches can run with `uv run --offline --script ...`. This WAV-only workflow does
not need FFmpeg. The pinned source and `.py.lock` travel with the script.

The PEP 723 block uses uv's dependency-metadata override to replace the pinned
Earshot 0.3.0 all-features dependencies with NumPy, SciPy, SoundFile, and soxr.
Do not remove the override, add a normal `pip install earshot`, or regenerate the
lock with full upstream dependencies. See [runtime.md](references/runtime.md)
when changing the pin or diagnosing setup.

## Choose the path

1. **Known sound:** query a relevant category/kind, then render an actual ID.
2. **Close, but needs a change:** use only knobs supported by that sound.
3. **New sound structure:** write a small Python recipe in the video project and
   render it with `custom`. No `forge` search or model critic is needed.
4. **A project's sound palette:** make a kit with a few roles and variants.

Use [sound-selection.md](references/sound-selection.md) for intent-to-category
selection; it is a short index, not a duplicate of the full bank. Query the
actual pinned bank instead of inventing IDs or assuming every member supports
every knob:

```bash
uv run --locked --script "$SKILL_DIR/scripts/earshot_sfx.py" list --kind whoosh
uv run --locked --script "$SKILL_DIR/scripts/earshot_sfx.py" list --category click
```

The unfiltered catalog is large. If needed, save its JSON to a project file and
inspect selected IDs/categories rather than loading the entire listing into
the conversation.

## Single effects and timing

```bash
uv run --locked --script "$SKILL_DIR/scripts/earshot_sfx.py" render whoosh_fast/crisp \
  --dur 0.8 --apex 0.32 --seed 42 --align peak --cue-at 3.0 \
  --out audio/sfx/transition.wav
```

This writes `transition.wav` and `transition.meta.json`. JSON is also returned on
stdout. `audio` describes the **written PCM file**, including duration, onset,
peak, end, sample rate, channels, hash, and technical checks. `render_meta` keeps
upstream knob results, including requested versus achieved apex/pitch. Read
these values before claiming a constraint was met.

`--cue-at` is the visual event time in seconds. `placement.start_s` is
`cue_at_s - anchor_s`, not the cue time itself. Align contacts to `onset`, a
whoosh's energy peak to `peak`, and a build resolving at a cut to `end`.
Negative starts are preserved as pre-roll; decide how the composition handles
pre-roll instead of silently clamping to zero. Peak is the loudest 5 ms RMS
window, not the largest individual sample.

Read [parameters.md](references/parameters.md) for duration fitting, pitch,
sample-rate changes, warning semantics, and exact output fields. Existing WAV
or metadata files are preserved unless `--force` is explicitly passed.

## Sound kits

The bundled `video-ui.json` is a small starting palette; the upstream `calm`,
`crisp`, and `minimal` presets are also available through `kit init`.

```bash
mkdir -p audio
cp "$SKILL_DIR/assets/kits/video-ui.json" audio/kit.json
# Edit this project copy: sounds, supported edits, seeds, takes, roles and levels.
uv run --locked --script "$SKILL_DIR/scripts/earshot_sfx.py" kit check audio/kit.json
uv run --locked --script "$SKILL_DIR/scripts/earshot_sfx.py" kit render audio/kit.json \
  --out audio/earshot-kit
```

Use a **dedicated generated-takes directory**: upstream kit rendering manages its
own previous takes there, including removing stale generated files. It writes
`kit.lock.json`; the wrapper adds `manifest.json` with absolute file paths,
measured timing and hashes. Matching takes are cached. Read each role's `align`,
`level_db`, actual seed and checks. Kit rerolls can change the planned seed;
the lock records the seed actually used. A valid kit configuration is separate
from a rendered kit whose individual takes have warnings.

## Custom effects

Read [custom-recipes.md](references/custom-recipes.md) when the bank cannot
express the request. Start with the runnable wooden-tap candidate if useful:

```bash
mkdir -p audio/recipes
cp "$SKILL_DIR/assets/recipes/wooden_tap.py" audio/recipes/my_tap.py
uv run --locked --script "$SKILL_DIR/scripts/earshot_sfx.py" custom \
  --recipe audio/recipes/my_tap.py \
  --params '{"body_hz":180,"duration":0.24,"texture":0.08}' \
  --seed 17 --out audio/sfx/my-tap.wav
```

The contract is `render(params, rng) -> numpy array` at **48 kHz**, mono or stereo.
The wrapper handles level, final fades, requested output rate, file writing,
measurement and metadata. Keep the source file with the project; the metadata
records its path, SHA-256, merged parameters and seed. Project recipes execute
Python code; use recipes you created or have inspected. Work in project files,
not inside the installed upstream package. Promote a recipe to this skill only
when maintaining a reusable recipe is part of the requested work.

## Hand off to HyperFrames or another video engine

- Generate before browser/video rendering; import the resulting WAV into the
  composition using that engine's normal media mechanism.
- Use a project-relative media path when the composition needs one. The wrapper
  returns absolute local paths so callers can locate artifacts reliably.
- Place at the measured `placement.start_s` or compute it from the kit's anchor.
  Keep source paths and hashes in the project's asset ledger when it has one.
- Keep individual effects separate from narration and BGM. The video/mix layer
  owns track gain, ducking, crossfades, pan, and final loudness.

`ok: true` means the command completed. `audio.checks.ok` and warning details
describe technical measurements; neither proves realism or taste. Do not add an
audio-understanding/model-scoring loop to ordinary generation. Reference-audio
understanding can use the host's existing audio-capable model when requested.
Complex scene audio or character performance may fit another available tool.

## Evaluation and maintenance

[evals/evals.json](evals/evals.json) contains realistic agent tasks and assertions.
Run the artifact checks without an audio model:

```bash
uv run "$SKILL_DIR/evals/run_evals.py" --suite smoke --out /tmp/earshot-eval
# Optional full pinned-bank rendering (keeps artifacts outside the skill):
uv run "$SKILL_DIR/evals/run_evals.py" --suite bank --out /tmp/earshot-bank-eval
```

See [evals/README.md](evals/README.md) for independent agent evaluation, listening
criteria, and the distinction between automated artifact checks and human taste.
