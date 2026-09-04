#!/usr/bin/env bash
# Create the Feishu human-eval document after lark-cli is configured and the user is logged in.
# Run from anywhere. Requires lark-cli on PATH and a completed `auth login` as user.
# Run without --yes first. Pass --yes only after the caller has shown the current
# high-risk action and parameters and received explicit user approval for this run.
set -euo pipefail

confirm_create=0
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--yes" ]; }; then
  echo "Usage: $0 [--yes]" >&2
  exit 2
fi
if [ "${1:-}" = "--yes" ]; then
  confirm_create=1
fi

ROOT="$(cd "$(dirname "$0")/fixtures/human-eval" && pwd)"
cd "$ROOT"

export LARKSUITE_CLI_NO_UPDATE_NOTIFIER=1
export LARKSUITE_CLI_NO_SKILLS_NOTIFIER=1

if ! command -v lark-cli >/dev/null 2>&1; then
  echo "ERROR: lark-cli is not on PATH" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required" >&2
  exit 1
fi

status_json="$(lark-cli auth status --json --verify 2>/dev/null || true)"
set +e
python3 - "$status_json" <<'PY'
import json, sys
raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    print("not_configured")
    raise SystemExit(2)
if data.get("ok") is False:
    print((data.get("error") or {}).get("subtype") or "unknown")
    raise SystemExit(2)
payload = data.get("data") or data
user = (payload.get("identities") or {}).get("user") or {}
if (
    payload.get("verified") is True
    or user.get("verified") is True
    or user.get("tokenStatus") in {"valid", "active", "ready"}
    or user.get("status") in {"valid", "active", "ready"}
    or (payload.get("identity") == "user" and (user.get("userName") or user.get("available")))
):
    print("ok")
    raise SystemExit(0)
print("user_not_logged_in")
raise SystemExit(3)
PY
auth_rc=$?
set -e
if [ "$auth_rc" -eq 2 ]; then
  echo "ERROR: lark-cli is not configured. Finish config init, then rerun." >&2
  exit 2
fi
if [ "$auth_rc" -eq 3 ]; then
  echo "ERROR: user identity is not logged in. Run: lark-cli auth login --domain docs --domain drive --domain wiki --as user" >&2
  exit 3
fi

echo "OK: auth looks usable, parsing eval-doc.xml"
parse_json="$(lark-cli docs +script --command parse --content @./eval-doc.xml --format json)"
python3 - "$parse_json" <<'PY'
import json, sys
data = json.loads(sys.argv[1])
if not data.get("ok"):
    raise SystemExit(f"parse command failed: {data}")
assessment = ((data.get("data") or {}).get("assessment") or {})
status = assessment.get("status")
print(f"parse assessment.status={status}")
if status not in (None, "pass", "passed", "ok"):
    diags = (data.get("data") or {}).get("diagnostics") or []
    print(json.dumps(diags, ensure_ascii=False, indent=2))
    if status in {"fail", "failed", "error"}:
        raise SystemExit(4)
PY

echo "Creating Feishu document as user"
create_args=(
  docs +create
  --doc-format xml
  --content @./eval-doc.xml
  --as user
  --parent-position my_library
)
if [ "$confirm_create" -eq 1 ]; then
  create_args+=(--yes)
fi
set +e
create_json="$(lark-cli "${create_args[@]}" 2>&1)"
create_rc=$?
set -e
if [ "$create_rc" -ne 0 ]; then
  echo "$create_json" >&2
  if [ "$create_rc" -eq 10 ]; then
    echo "CONFIRMATION REQUIRED: show the high-risk action and parameters to the user." >&2
    echo "After explicit approval, rerun this script with --yes." >&2
  fi
  exit "$create_rc"
fi

doc_meta="$(python3 - "$create_json" <<'PY'
import json, sys
raw = sys.argv[1]
start = raw.find("{")
data = json.loads(raw[start:])
if not data.get("ok"):
    raise SystemExit(f"create failed: {raw}")
doc = ((data.get("data") or {}).get("document") or {})
url = doc.get("url") or ""
doc_id = doc.get("document_id") or ""
print(f"{url}\t{doc_id}")
PY
)"
IFS=$'\t' read -r DOC_URL DOC_ID <<< "$doc_meta"
if [ -z "${DOC_URL:-}" ]; then
  echo "ERROR: create succeeded but no document URL" >&2
  exit 5
fi
echo "DOC_URL=$DOC_URL"
echo "DOC_ID=$DOC_ID"

work_dir="$(mktemp -d "${TMPDIR:-/tmp}/feishu-human-eval.XXXXXX")"
echo "Fetching document back with ids"
lark-cli docs +fetch --doc "$DOC_URL" --detail with-ids --as user --doc-format xml --format json \
  > "$work_dir/fetch.json"
python3 - "$work_dir" <<'PY'
import json
import re
import sys
from pathlib import Path
work_dir = Path(sys.argv[1])
raw = (work_dir / "fetch.json").read_text(encoding="utf-8")
start = raw.find("{")
data = json.loads(raw[start:])
if not data.get("ok"):
    raise SystemExit(f"fetch failed: {raw[:1000]}")
payload = data.get("data") or {}
doc = payload.get("document") or payload
content = doc.get("content") or payload.get("xml") or ""
text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
whiteboard = text.count("<whiteboard")
html5 = text.count("<html5-block")
print(f"FETCH_WHITEBOARDS={whiteboard}")
print(f"FETCH_HTML5={html5}")
found = re.findall(r'<whiteboard[^>]*\btoken="([^"]+)"', text)
print(f"BOARD_TOKENS={len(found)}")
for token in found:
    print(f"BOARD_TOKEN\t{token}")
(work_dir / "board-tokens.txt").write_text("\n".join(found) + "\n", encoding="utf-8")
if whiteboard < 1 and not found:
    raise SystemExit("fetch-back did not find whiteboard blocks")
PY

mkdir -p "$work_dir/previews"
if [ -s "$work_dir/board-tokens.txt" ]; then
  i=0
  (
    cd "$work_dir"
    while IFS= read -r token; do
      [ -z "$token" ] && continue
      i=$((i + 1))
      echo "Exporting preview $i $token"
      lark-cli whiteboard +export \
        --whiteboard-token "$token" \
        --output-type preview \
        --output "./previews/board-$i.jpg" \
        --overwrite \
        --as user || true
    done < "$work_dir/board-tokens.txt"
  )
fi

echo "HUMAN_EVAL_DOC_URL=$DOC_URL"
echo "OK: created and fetched. Evidence in $work_dir"
