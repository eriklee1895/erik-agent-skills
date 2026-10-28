# Runtime packaging and updates

The PEP 723 script imports a complete immutable upstream snapshot. The skill
does not vendor a partial fork, virtual environment or model weights.

- Source: <https://github.com/Leonxlnx/earshot>
- Pin: `925ebe56a1b755e5d354ab642bb8f344440cfa9c`, package `0.3.0`.
- Upstream license: MIT; preserve it when redistributing upstream code.
- Python 3.11–3.14; uv 0.12.5+; Git for initial source fetching.
- Upstream declares Torch/Transformers as basic dependencies.
  `[[tool.uv.dependency-metadata]]` inside the script overrides that version's
  requires-dist with NumPy, SciPy, SoundFile, soxr. This is a uv extension in
  valid PEP 723 metadata, not universal pip behavior.
- Git pinning is intentional: uv 0.12.5 ran a static-metadata direct sdist but
  could not lock it without artifact metadata. The pinned Git source locks
  and runs without an installation/bootstrap script.

Modules named `earshot.forge.bank`, `.kit`, `.dsp` are used by generation;
the namespace does not mean the model-scored forge command runs. Do not delete
that directory. Fitted bank entries also use pure-DSP code under `.fit`, without
performing a new recording fit or invoking CLAP.

`doctor` reports installed distributions and loaded heavy modules. The wrapper
refuses a runtime containing/loading Torch or Transformers. First use fetches
source and native wheels; warmed caches are reused. DSP render time excludes
that cold-start preparation. Production images can warm the environment using
doctor, then use `uv run --offline --script ...` with cached Python and packages.

For a host that uses a frozen project environment instead of per-script uv
environments, put the same Git pin and dependency-metadata override in that
project's dependency configuration and lock. Execute the script with that
interpreter (`uv run python ...`), which does not resolve its inline metadata.
Keep runtime installs disabled according to the host's deployment contract.
The numerical and audio libraries contain native code; this path avoids model
frameworks and weights, not all native dependencies or installation cost.

Keep `earshot_sfx.py.lock` adjacent to the script. Deliberate dependency updates:

```bash
uv lock --script "$SKILL_DIR/scripts/earshot_sfx.py" --upgrade
uv run --locked --script "$SKILL_DIR/scripts/earshot_sfx.py" doctor
```

Inspect lock changes for unwanted model/CUDA packages. A new source pin requires
checking version, import graph, bank/kit behavior and metadata override, then
running smoke evals, full-bank rendering, seed repeatability and independent
agent tasks. Recheck behavior before expanding supported Python versions.

Commands return JSON on stdout; failures exit nonzero. UV setup logs use stderr.
WAV reads/writes use SoundFile; FFmpeg is not required. Other upstream audio
analysis commands may follow additional tool/model paths and are outside scope.

Primary references:

- [uv scripts and locks](https://docs.astral.sh/uv/guides/scripts/)
- [uv dependency metadata](https://docs.astral.sh/uv/reference/settings/#dependency-metadata)
- [Pinned SFX contract](https://github.com/Leonxlnx/earshot/blob/925ebe56a1b755e5d354ab642bb8f344440cfa9c/docs/SFX.md)
