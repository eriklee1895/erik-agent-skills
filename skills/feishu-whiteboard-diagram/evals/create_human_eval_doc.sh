#!/usr/bin/env bash
# Create the Feishu human-eval document after lark-cli is configured and the user is logged in.
# Run from anywhere. Requires lark-cli on PATH and a completed `auth login` as user.
set -euo pipefail

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
if not data.get("ok"):
    print((data.get("error") or {}).get("subtype") or "unknown")
    raise SystemExit(2)
payload = data.get("data") or data
user = (payload.get("identities") or {}).get("user") or {}
if (
    payload.get("verified") is True
    or user.get("tokenStatus") in {"valid", "active"}
    or user.get("status") in {"valid", "active"}
    or (payload.get("identity") == "user" and user.get("userName"))
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
set +e
create_json="$(lark-cli docs +create --doc-format xml --content @./eval-doc.xml --as user --parent-position my_library 2>&1)"
create_rc=$?
if [ "$create_rc" -eq 10 ]; then
  echo "confirmation required; retrying with --yes because the user asked to create this eval doc"
  create_json="$(lark-cli docs +create --doc-format xml --content @./eval-doc.xml --as user --parent-position my_library --yes 2>&1)"
  create_rc=$?
fi
if [ "$create_rc" -ne 0 ]; then
  echo "$create_json" >&2
  echo "retrying without parent-position" >&2
  create_json="$(lark-cli docs +create --doc-format xml --content @./eval-doc.xml --as user --yes 2>&1)"
  create_rc=$?
fi
set -e
if [ "$create_rc" -ne 0 ]; then
  echo "$create_json" >&2
  exit "$create_rc"
fi

python3 - "$create_json" <<'PY'
import json, sys
raw = sys.argv[1]
start = raw.find("{")
data = json.loads(raw[start:])
if not data.get("ok"):
    raise SystemExit(f"create failed: {raw}")
doc = ((data.get("data") or {}).get("document") or {})
url = doc.get("url") or ""
doc_id = doc.get("document_id") or ""
print(f"DOC_URL={url}")
print(f"DOC_ID={doc_id}")
blocks = doc.get("new_blocks") or []
print(f"NEW_BLOCKS={len(blocks)}")
for block in blocks:
    print(f"BLOCK\t{block.get('block_type')}\t{block.get('block_id')}\t{block.get('block_token')}")
if data.get("data", {}).get("warnings"):
    print("WARNINGS=" + json.dumps(data["data"]["warnings"], ensure_ascii=False))
PY
