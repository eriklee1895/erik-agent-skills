# Seedream 5.0 Flash

ID: `doubao-seedream-5-0-flash-260915`; aliases include `flash`, `seedream-flash`, `5-flash`. Pro remains the default. Lite is retired from this skill; old aliases/IDs produce an explicit migration error rather than being redirected.

Flash uses the same endpoint, ten-reference limit, native size range, editing protocol, transparent-image option and layer-decomposition mode as Pro. Its optimization mode is **standard only**; Pro also offers fast. Neither active model offers the former model's web search, sequential storyboards or streaming.

Always default to Pro. Flash is an option only when the user explicitly selects it or authorizes a faster/lower-cost replacement; a draft, UGC or batch alone does not authorize switching. The official price, rechecked 2026-10-25, is CNY0.12 per output including each decomposed layer. See the [120-request study](../evals/comprehensive-benchmark.md) for task-specific timing and prompt observations; they do not override the user's model preference or establish universal quality parity.

Both accept 1K, 1.5K, 2K and valid explicit pixels. Use 1.5K for an economical intermediate tier, 2K for fine text/detail, and exact WxH when a downstream layout requires pixels. A short Chinese headline is not automatically a reason to reject Flash; inspect the actual [benchmark examples and limitations](../evals/flash-benchmark.md).

Transparent output requires editing one existing alpha image with PNG output. To isolate an object in an opaque picture, [decompose it](transparent-layers.md) first. The layer mode returns a base plus up to sixteen PNG foregrounds with position metadata, not a PSD file.

For portable content controls, write constraints naturally in the prompt. Flash does not receive the undocumented Pro negative_prompt default. The explicit no-people/no-text guards become prompt clauses; they are soft instructions, not hard exclusions.

The old 3K/4K presets and fourteen-reference behavior do not transfer from Lite. Nor do its old timing/text-quality observations. See the [current API source check](api-reference.md) and [migration/benchmark protocol](../evals/flash-migration-plan.md).
