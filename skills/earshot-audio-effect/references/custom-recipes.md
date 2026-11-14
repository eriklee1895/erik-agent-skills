# Design a project DSP recipe

Use this when supported bank knobs cannot express the sound. Ask only about
consequential missing creative requirements; scene/timing context often gives
enough direction to produce a candidate.

1. Identify action and sync: contact, velocity maximum, release or resolution.
   Specify file duration and audible tail separately.
2. Split into causal layers: contact transient, resonant body, friction/air,
   optional release and room. A click need not contain every layer.
3. Name parameters/ranges meaningful for this recipe (body frequency, decay,
   friction strength). Reject invalid values rather than silently ignoring them.
4. Render a candidate, inspect written-file timing/checks, and offer playback
   when creative judgement matters. Change the relevant layer for feedback.
5. Keep recipe, parameters, actual seed and WAV with the project. A future model
   can improve a new recipe without silently changing an old one.

## Executable contract

Copy `assets/recipes/wooden_tap.py` into the project for a complete runnable
starting point. A recipe may define `DEFAULTS`, and must define
`render(params, rng)` returning a NumPy array at **48 kHz**, shape `(frames,)`,
`(frames, 1)` or `(frames, 2)`.

`custom` merges JSON params over DEFAULTS, supplies `dsp.rng(seed)` and calls
the function. Use that RNG for noise/jitter; global randomness, wall clock,
network/model calls defeat this generation path's contract.

The wrapper validates the signal, applies `--fade-in` (default .001 s),
`--fade-out` (default .02 s) and `--peak-db` (default -3), then resamples if
requested and writes PCM_24. Set fades to zero only when deliberately handled
inside the recipe. JSON parameters must actually affect the recipe; a recorded
parameter does not prove it was consumed. The recipe controls file duration.
Python prints during recipe import and rendering are routed to stderr, keeping
the wrapper's stdout available for its JSON result.

## DSP building blocks (48 kHz)

Import `from earshot.forge import dsp`:

| Building block | Signature / intent |
| --- | --- |
| Noise | `dsp.noise(seconds, rng, color='white')` |
| Decaying body | `dsp.modal(freqs, decays, amps, seconds, rng, jitter=0.003)` |
| Envelope | `dsp.env_exp(seconds, tau, attack=0.0005)` |
| Filter | `dsp.butter(x, 'band', (low_hz, high_hz))`, or low/high |
| Tone / sweep | `dsp.osc(freq, shape='sine', seconds=...)`, `dsp.sweep(f0, f1, seconds)` |
| Moving filter | `dsp.svf(x, cutoff, q=0.7, mode='band')` |
| Room | `dsp.room(x, rng, rt60=0.25, size=0.5, damp=0.6, wet=0.12)` |
| Stereo | `dsp.pan_to_stereo(x, pan=0.0)`, `dsp.stereo(x, rng, width=0.3)` |

- **Less metallic contact:** change resonant ratios/decays, reduce high-Q ringing;
  merely lowering gain changes level rather than material.
- **Heavier landing:** emphasize lower body modes and a short surface transient;
  avoid a long pre-swell when contact must be immediate.
- **Paper gesture:** filtered noise, asymmetric gesture envelope, small friction
  fluctuations. Complex realistic handling may suit another tool/recording.
- **Cartoon spring:** decaying pitch motion plus body resonance; design a new
  gesture rather than applying a pitch knob to a noise whoosh.

No forge search, recording fit, or model scoring is required. Host VLM audio
understanding is optional when reference-audio analysis is actually requested.
Technical checks cannot certify realism, beauty or story fit.
