# Batch execution and recovery

Read this for JSONL preparation, preflight, output reservations, and retrying
failed jobs. Run examples from the skill directory, or use the script's full
path; input/reference paths resolve from the current working directory.

Use `aspect_ratio` in JSONL. Legacy `aspect` remains accepted; if both keys are
present, their values must match. The `generate` / `edit` CLI flag is still
`--aspect`.

`prompt` is required and must be a non-empty string. Defaults apply only when a
field is omitted: model=`sunburst`, aspect_ratio=`1:1`, n=1, GPT quality=`auto`,
banana resolution=`1K`, images=[]; unnamed outputs use `job-000`, etc., based on
the physical zero-based row. Explicit nulls, empty strings, invalid types or
model values, dialect mismatches, and unknown fields (including typos) are
errors. `images` must be a list of reference path strings; paths resolve from
the current working directory, as they do for `--image`. Blank lines and lines
starting with `#` are ignored.

`name` is a filename stem, not a path: no `/`, `\`, NUL, `.` or `..` names.
Output names must not collide within a batch (case-insensitive), including
numbered variants, their possible PNG/JPEG/WebP extensions, metadata, and the
reserved `batch-summary.json`.
For n>1, previews list `name-1.png`, `name-2.png`, etc.; actual extensions
follow the returned image bytes. Providers may return fewer
than n images; one returned image uses `name.png`, and the summary records the
actual saved paths. Existing images at chosen targets are overwritten; use a
fresh output directory to keep older runs.

The entire batch is parsed, validated, and its references loaded before the
first API call. An invalid row reports its physical **1-based line number** and
stops the batch before any API calls or output writes. `--dry-run` performs the
same preflight and prints JSON with each job's line, name, model alias, normalized
request, and expected output paths. Existing directories at file targets and
file parents are rejected before execution. Preflight cannot predict provider
failures or later filesystem changes.

Batch execution is sequential. `batch-summary.json` is replaced atomically
after each attempted job, before the next API call. Each entry includes `name`,
`line`, `model`, `status`, actual `outputs`, `cost`, and `elapsed_seconds`; failures
also have `error_type`. `cost: null` means no cost was reported, not zero spend.
HTTP, network, and malformed-response errors are recorded and later jobs can
continue. A local save failure stops the batch to avoid more paid calls; the
summary contains only attempted jobs and retains any saved paths and known cost.
Execution exits 0 when all jobs succeed and 1 if any job fails.

Requests are attempted once, with no automatic retries. Before retrying, inspect
the summary and saved metadata and create a JSONL containing only the jobs you
want to retry. A timeout alone does not establish the final server outcome;
check OpenRouter's activity records when cost is unknown. Images are decoded and
saved one at a time; if a later item is malformed, completed images and reported
cost remain in the summary. Checks cover JSON/data/base64 and supported raster signatures, not visual
quality or pixel dimensions. JSON checkpoints preserve existing file permissions.

Offline regression tests (standard library only):

```bash
python3 -m unittest discover -s tests -v
```
