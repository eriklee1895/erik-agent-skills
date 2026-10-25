# Parameters and measured output

All commands here use `uv run --locked --script "$SKILL_DIR/scripts/earshot_sfx.py"`.

| Option | Meaning / boundary |
| --- | --- |
| `--seed N` | Fixed integer noise/jitter seed. Omitted for bank rendering uses the tuned member's own seed. Keep the pin, dependency versions, parameters and seed; retain delivered WAV/hash for exact old-project playback. |
| `--dur S` | Requested **file** duration, positive seconds. Whoosh-family recipes scale their gesture; others use supported parameter fitting, then fade/trim/pad as needed. It does not promise S seconds of audible content. Read `render_meta.edits.dur`. |
| `--apex S` | Target time of the loudest 5 ms RMS window, 1 ms hop. Whoosh family only. With dur, require `0 <= apex < dur`. Read achieved value and error; never substitute the request for a measurement. |
| `--pitch NOTE_OR_HZ` | Supported members only: `E5`, `Fs4`, `440hz`. Noise-led whooshes, swipes, keys and glitches generally reject it; some members have their tonal layer disabled. Check catalog knobs and `render_meta.edits.pitch`. |
| `--peak-db DB` | Output sample-peak target, default **-3 dBFS**, at most 0. Reapplied after output resampling. Not integrated LUFS or final-mix gain. |
| `--weight W` | Bank only; positive amplitude multiplier (doubling adds 6 dB). Combined with peak_db, must stay within full scale. |
| `--sr RATE` | 44100, **48000** default, 88200 or 96000 Hz. Native DSP is 48 kHz; soxr resamples output. Timing is remeasured on written PCM. |
| `--align onset\|peak\|end` | Which measured feature aligns with a visual cue. Default onset. |
| `--cue-at S` | Visual cue time; reports start = cue - measured anchor. Negative starts retain pre-roll. |
| `--force` | Allow replacement of an existing WAV/sidecar, or force kit regeneration. Use new paths for candidates to compare. |

## Metadata contract

Single renders write PCM_24 `.wav` and adjacent `.meta.json`, and return the same
JSON on stdout. Failures return `ok:false`, `error`, `error_type` and nonzero exit.
UV setup logs use stderr.

- `source`: bank ID or project recipe path/hash, actual seed and parameters.
- `audio.file`, `sha256`, `frames`, `sr`, `channels`, `subtype`: written artifact.
- `audio.duration_s`: frame-exact duration, frames / sr.
- `audio.dur_s`, `onset_s`, `peak_s`, `end_s`: upstream conventions. Onset uses
  a 1 ms envelope within 30 dB of its maximum. Peak is the center of the loudest
  5 ms window. End is the end of the last 5 ms window within 50 dB of peak.
- `audio.checks`: technical warnings/notes. Top-level ok means command completion.
- `render_meta`: bank rendering's seed, edits and upstream checks.
- `placement`: selected anchor and derived file start when requested.
- `runtime`: source pin, bank version, package versions and absence checks.

For a peak at 0.3195 s and visual cue at 3 s, start at **2.6805 s**. The source
still contains its approach and decay. If it starts before the composition,
retain pre-roll or consciously trim/shift in the composition; silent clamping
loses synchronization.

`check FILE.wav` uses SoundFile and local measurements, with no ASR, description,
realism classification or model scoring. Warnings include clipping, edges, DC,
ringing, cut tails, silence, and category-specific patterns. Some are deliberate
design choices; report them and do not claim a successful command proves taste.

Kits preserve `kit.lock.json` and add `manifest.json`. Assets add `role`, `sound`,
`seed`, `align`, `level_db` to the measured file fields. The video's mix layer
applies the role's gain; output peak level is separate from mix level.

Nonnative-rate kit takes are normalized to the effective role peak after
resampling and before PCM encoding. The lock's timing, level and checks are
updated from the written WAV. A `skill_renderer_revision` in the lock records
this output policy; older resampled kit caches are regenerated once, since
normalizing an already clipped PCM file cannot restore its waveform.
Kit `edits.peak_db` keeps the upstream default of -1 dBFS; the single-effect
CLI's default is -3 dBFS. Role `level_db` remains a separate mix instruction.

`kit check KIT.json` validates configuration and renders its candidates in memory;
unreadable/invalid configurations and render errors exit nonzero. A valid kit
with technical warnings completes with the warnings in `checks`. Rendered kit
files are remeasured during `kit render`; individual files can use `check`.
