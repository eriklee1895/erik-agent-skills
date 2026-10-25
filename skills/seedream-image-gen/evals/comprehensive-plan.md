# Comprehensive Pro / Flash prompt benchmark

## Spec and global constraints

The user approved a comprehensive benchmark on 2026-10-25 and removed the proposed monetary ceiling. Unspecified image requests must always default to Pro; Flash requires explicit selection or an explicit speed/cost preference. Results improve prompts and workflows, never silently change that default.

The initial design is eighteen cases, two independent samples each for Pro standard and Flash standard (72 calls), plus two Pro-fast samples on four cases (8 calls). Fixed prompts, synthetic references, size, output format and negative-default settings are shared within each comparison. Use six local workers and a fixed shuffled order. Concurrency is an experimental control, not a provider limit. No hardcoded IPM schedule or spending ceiling. Record usage and list-price estimates. Unknown paid submissions are never replayed.

Judge composition/style, exact text, edit scope, reference adherence, transparency and layer reconstruction separately. Publish every planned case including failures and uncertainty. Hidden-model contact sheets reduce label bias but are not independent human double-blind judgments. Two samples establish case-level observations, not population quality rankings. Original images, credentials and expiring URLs stay outside Git; only portable prompts, hashes, measurements and review records belong in the skill.

## Task 1: Freeze the suite and extend the runner

Create an immutable eighteen-case suite with explicit criteria and repeat indices. Reuse the existing single-submission worker and safe journals. Add marker/format argument support and exclude annotated reference previews from generated-output counts. Preserve the original sixteen-case suite. Add failing offline contracts first, then implement and run the entire Seedream test suite.

Interfaces: suite preparation produces cases.json plus hashed fixtures; the runner consumes case IDs, command/model/mode/size/prompt/references and optional marker/background fields. The analysis consumes journals and actual outputs, not successful-only subsets.

Expected: eighty unique requests, eighteen cases, two repeats for each standard model, eight extra fast cases; preparation never calls an API or rewrites existing evidence. All offline tests pass.

## Task 2: Execute and inspect all planned samples

Prepare a new outside-Git study directory. Check official pricing and endpoint without printing credentials. Run a four-request smoke slice, then execute the rest while skipping existing journals. Inspect every result, generate shuffled anonymous contact sheets, extract OCR and local geometry/alpha measurements, and keep all failure states. Select at most a few concrete prompt weaknesses for controlled before/after comparisons; use new case IDs and a separate journaled study for intentional follow-ups.

Expected: complete accounting for every planned case and actual request/output count, model/task timing summaries, rubric scores and limitations. No automatic paid replay. Additional requests require a recorded hypothesis, not a missing-response retry.

## Task 3: Incorporate verified prompt improvements and publish

Update only guidance supported by this round's evidence: coordinate/marker editing, explicit reference roles, typography, style instructions, layer requests and common failure handling as observed. Preserve Pro as the default everywhere, including model routing prose. Save reproducible redacted results, report and prompt deltas. Run tests, Ruff, skill validation, links and privacy checks, then one fresh final review and a single verified fix pass if needed. Update PR #51; do not merge without user instruction.

Expected: actionable prompt guidance tied to concrete paired cases, all validations green, review findings accounted for and PR head verified.

## Review focus

Check that the eighty-case accounting is complete; annotations are not counted as generated outputs; prompts/references/size are comparable; no model wins are inferred from OCR alone; unknown submissions are not replayed; images, signed URLs, credentials and personal paths are not published; and no prose or runtime route chooses Flash for unspecified requests. Verify any follow-up hypothesis against all paired outputs, including unsuccessful attempts.
