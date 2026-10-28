# Choosing sounds

Query `earshot_sfx.py list --category CATEGORY` or `list --kind ROLE` through
`uv run --locked --script`. Omit filters to inspect the complete bank. The pinned bank
currently has 201 entries; the live query, not this index, is authoritative.
Rows include IDs, measured times, kinds, supported knobs, and notes. `fit/*`
entries also retain their source information: they are procedural reconstructions,
not embedded recordings.

| Picture / intent | Start with | Anchor / selection considerations |
| --- | --- | --- |
| Cursor press / touch | `click`, `pro_click`, `tap` | onset; one consistent voice per interaction family |
| Switch or latch | `toggle` | onset; some members have a deliberate press/release structure |
| Card or bubble appears | `pop`, `pro_pop_in`, `tap` | onset/contact; choose restrained or playful by the brief |
| Motion / short transition | `whoosh_fast`, `swish`, `swipe` | peak on strongest move; inspect dur/apex support |
| Larger pass | `whoosh_big`, `pro_whoosh_big` | peak; low-frequency weight may mask narration |
| Confirmation / tuned accent | `notify`, `pro_notify`, `pluck` | onset; use supported pitches to match a palette |
| Sparkle / sustained reveal | `shimmer`, `pro_shimmer` | a relevant peak/end; keep long tails deliberate |
| Contact / landing | `tap`, `impact`, `pro_impact` | onset; distinguish contact from a swelling cinematic hit |
| Build / release | `riser`, `downlifter`, `sub_drop` | often end/peak; read the actual timing |
| Typing / key | `typing_key`, `pro_typing_key`, `pro_typing_run` | individual contact or a run; seed variants |
| Digital disruption | `glitch`, `pro_glitch` | discontinuities/silence may be deliberate; retain check notes |
| Paper / cloth gesture | `swipe`, `swish` | a procedural candidate; custom structure for a specific action |

Identify **source/material + action + character + timing**. “A dry light wood tap
at contact” is more actionable than “a cool logo sound.” Select an actual ID
before tuning. “Warmer” may mean another member or a new body/noise balance,
not a universal `warmth` parameter.

Use a few candidates when the creative choice is consequential. Label them by
recipe/parameters and provide local playback; do not claim one sounds more
realistic or beautiful based solely on a technical check. For new sounds,
consult [custom-recipes.md](custom-recipes.md).

The bundled kit `assets/kits/video-ui.json` defines a modest UI/motion palette.
Edit a project copy; do not add a sound to every animation merely because a kit
has a matching role.
