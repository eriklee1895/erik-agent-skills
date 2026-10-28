# Validation evidence

## PR review validation

The reviewed revision supports Python 3.11–3.14. Fresh execution covered macOS
ARM64 / Python 3.14.7 / uv 0.12.5 and Linux x86_64 / Python 3.14.9 / uv 0.13.5,
using the adjacent lock and the same immutable Earshot 0.3.0 Git pin.

| Check | Observed result |
| --- | --- |
| macOS Python 3.14 integration tests | 14 / 14 passed |
| macOS artifact smoke suite | 16 / 16 passed with cached/offline uv execution |
| Linux Python 3.14 integration tests | 14 / 14 passed with cached/offline uv execution |
| Linux full artifact suite | 17 / 17 passed: 16 smoke cases + 201 / 201 bank renders |
| Linux bank technical warnings | 16 entries retained warnings; not presented as aesthetic failures or hidden |
| Fresh Linux uv cache | Installed 8 runtime distributions; no Torch/Transformers installed or loaded |
| Skill validation, Ruff lint/format, compilation, lock consistency and bilingual catalog | Passed |

Independent code review reproduced a nonnative-rate kit defect: resampling a
legal 0 dBFS take could exceed full scale before PCM encoding. The adapter now
normalizes before encoding, records measurements from delivered PCM, and
regenerates older resampled caches once. New regressions cover weighted peaks,
lock/file consistency and cache reuse. Custom-recipe Python diagnostics now go
to stderr, preserving stdout JSON. The targeted independent re-review found
no remaining actionable issues, subject to the execution checks above.

The four Agent-use cases below are historical evidence, not newly rerun Agent
evals for this review. No new human listening, aesthetic score, final-video or
production-runtime acceptance is claimed. Generated audio and machine-specific
logs remain outside the published skill.

## Historical validation — 2026-10-23

Tested on macOS ARM64, uv 0.12.5, Python 3.13.7, Earshot 0.3.0 at
`925ebe56a1b755e5d354ab642bb8f344440cfa9c`. Other platforms/Python branches
have lockfile resolutions but were not executed in this validation.

| Check | Observed result |
| --- | --- |
| New uv cache / initial fetch and installation | Success; 8 runtime distributions, no Torch/Transformers installed or loaded |
| Integration tests | 11 / 11 passed, including resampling peaks and invalid kit configuration regressions |
| Automated artifact eval | 14 / 14 smoke cases passed |
| Complete pinned bank | 201 / 201 rendered and decoded; 185 without warnings, 16 with retained upstream technical/style warnings |
| Full artifact suite | 15 / 15 checks passed (14 smoke cases + complete-bank check) |
| Independent agent tasks | 4 / 4 completed: new spring recipe, supported-knob tuning, scene-audio routing, timeline handoff |
| Skill validation / Ruff / compilation / lock consistency | Passed |
| Human listening / final video acceptance | Not performed; no taste or realism score claimed |

The Whoosh case wrote 38,400 frames at 48 kHz (0.8 s), with a measured RMS peak
at 0.3205 s for a requested 0.32 s. File start was computed from that measurement.
The output-rate case wrote 28,665 frames at 44.1 kHz (0.65 s). Kit repetition
reused all 10 takes. Two independently authored 0.6 s spring variants were
rendered, checked, and reproduced with identical hashes per variant.

The independent no-skill baseline also succeeded on its single Whoosh task.
It used source inspection and a custom source-loading script; this is not
evidence of a failed baseline or a quantitative improvement over an agent.

Code review found two issues that the first smoke set missed: output-rate
resampling changed the requested sample peak, and invalid kit checks reported
command success. Both received failing regression cases, fixes, and independent
re-verification. Final-output normalization preserves the effective weighted
target; invalid configuration fails while technical warnings remain separate.

This minimal runtime omits optional Numba/JIT. Times include process startup,
synthesis, checks and metadata: the 0.8 s Whoosh eval took about 7.1 s, and the
kit-plus-cache eval about 20.1 s in this run. These are workload observations,
not a rendering-only benchmark or an all-effects subsecond claim. The complete
bank check used four workers and took about 218 s. WAV reuse is immediate at
the mix layer; kit cache avoids repeating matching synthesis.

Generated audio, detailed logs and machine-specific manifests remain outside
the published skill. Use `run_evals.py` for fresh evidence in a new output folder.
