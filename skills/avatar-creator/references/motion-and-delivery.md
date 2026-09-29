# Motion and delivery

## Self-contained animation recipe

Use this skill's `scripts/animate_avatar.py`. It calls Ark directly and does not
import, invoke, or require any other skill. Runtime requirements: Python 3.10+,
`uv` (for declared Python dependencies), `ffmpeg`, `ffprobe`, and `ARK_API_KEY`.
The script supports macOS/Linux file locking. Set credentials in the environment
or the working directory's `.env`; environment values take precedence.
`ARK_BASE_URL` optionally selects an HTTPS Ark-compatible endpoint. Cleartext
HTTP is accepted only for loopback hosts used by offline tests; credentials and
query/fragment components are rejected.

Only a local PNG, JPEG, or WebP is accepted. Use the selected single-character
master, not the entire candidate sheet. Both first and last frames use the same
image bytes. Fixed settings: `doubao-seedance-2-5-260628`, 10 seconds, 720p,
`ratio=adaptive`, no audio, no watermark. These defaults are a maintained preset,
not user-facing model-selection questions.

The following prompt is sent **verbatim**, including punctuation and “过程种”:

```text
角色非常灵动的挥挥手，傻傻的转一圈，然后凑到镜头上，再回去。
整个过程种，镜头不允许有任何的 zoom 或者 move 等动作，镜头固定。角色一直都保持“运动”而非“静止”状态。
```

Do not append identity locks, negative prompts, timing instructions, or rewritten
actions. The selected image supplies the character; the script owns the recipe.
The CLI intentionally has no prompt, model, duration, or resolution override.
If the user explicitly requests a different action, duration, provider, or
transparent output, explain that the preset does not meet that requirement and
resolve it before a paid call. Ordinary “做动图” in an established character
conversation can proceed directly with this preset.

## Run and resume

Resolve `SKILL_DIR` to this skill's installed directory. Run from the user's
project so its `.env` and relative output paths resolve correctly.
The script's dry run makes no Ark request; `uv` may still access the network
to resolve or download Python dependencies on startup.

```bash
# Script preflight: no Ark call, credentials, ffmpeg, or output mutation.
uv run "$SKILL_DIR/scripts/animate_avatar.py" \
  --image output/character-master.png --out output/avatar-motion --dry-run

# One generation task, then download and export both formats.
uv run "$SKILL_DIR/scripts/animate_avatar.py" \
  --image output/character-master.png --out output/avatar-motion

# Continue the saved task or finish local export; never creates another task.
uv run "$SKILL_DIR/scripts/animate_avatar.py" \
  --resume --out output/avatar-motion
```

Output directories belong to one run; use a new directory only for a genuinely
new, authorized generation. A saved run cannot be replaced with a new image.
`--poll-interval` defaults to 20 seconds and `--max-wait` to 1800 seconds; a local
wait timeout does not cancel the remote task. Resume from the same directory.

The script writes `manifest.json` before submission and saves the returned task
ID immediately. It never automatically retries POST. If submission outcome is
unknown, keep the run directory and reconcile the task in the provider console.
Once the correct ID is known, attach it with:

```bash
uv run "$SKILL_DIR/scripts/animate_avatar.py" \
  --resume --out output/avatar-motion --task-id YOUR_EXISTING_TASK_ID
```

This attaches an existing task; it does not submit or verify that the recovered
task used the intended reference. Check the provider record before attaching.
Never guess an ID or start a replacement merely because a request timed out.
Failed/cancelled/expired tasks stay terminal. GET/download failures and local
encoding failures are recoverable through the same `--resume` command.

Outputs: `source.mp4` (provider original), `avatar.mp4` (H.264 playback copy),
`avatar.gif` (480px maximum side, 15 fps, infinite repeat), `prompt.txt`, input
snapshot, and `manifest.json` with task status, preset, image hash, and file checks.
GIF/MP4 exports are opaque; a transparent input does not create transparent video.
Keep generated files, credentials, and runtime state out of published skill source.

## Inspect the result

Technical export success does not prove visual quality. Preview at least three
cycles, inspecting the wave, full turn, approach, return, camera stability,
identity, limbs, and cropping. Compare the end/start and neighboring motion for
a jump, unnatural pause, fur flicker, or shadow change. Same-image endpoints do
not guarantee velocity continuity. If only extracted frames were inspected,
state that limit instead of claiming a visually seamless loop.

Do not secretly change the fixed recipe when an action is weak. Report which
action or seam failed; another paid generation must fit the user's remaining
authorization. Deliver the actual GIF and MP4 paths, not only the task ID.

The preset API subset was derived from this repository's existing Seedance client;
future maintenance should verify the [create](https://www.volcengine.com/docs/82379/1520757)
and [query](https://www.volcengine.com/docs/82379/1521309) contracts directly.
