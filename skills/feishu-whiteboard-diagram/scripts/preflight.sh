#!/usr/bin/env bash
# preflight.sh — verify Node, whiteboard-cli, and optionally lark-cli.
set -euo pipefail

ok() { echo "OK: $*"; }
warn() { echo "WARN: $*" >&2; }
fail() { echo "ERROR: $*" >&2; exit 1; }

if ! command -v node >/dev/null 2>&1; then
  fail "node not found. Install Node.js 20+."
fi
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$NODE_MAJOR" -lt 20 ]; then
  fail "Node.js 20+ required, found $(node -v)."
fi
ok "node $(node -v)"

if ! command -v npx >/dev/null 2>&1; then
  fail "npx not found."
fi

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 not found. It is required by scripts/lint_svg.py."
fi
ok "python3 $(python3 --version 2>&1)"

if ! WB_VER="$(npx -y @larksuite/whiteboard-cli@^0.2.13 -v 2>/dev/null)"; then
  fail "Cannot run @larksuite/whiteboard-cli@^0.2.13 via npx."
fi
ok "whiteboard-cli ${WB_VER}"

if command -v lark-cli >/dev/null 2>&1; then
  if lark-cli --version >/dev/null 2>&1; then
    ok "$(lark-cli --version 2>/dev/null | head -n1)"
  else
    warn "lark-cli is on PATH but --version failed."
  fi
else
  warn "lark-cli not on PATH. Local SVG/DSL preview still works; Feishu write needs:"
  echo "         npm install -g @larksuite/cli" >&2
  echo "         lark-cli config init --new && lark-cli auth login" >&2
  echo "         plus lark-doc / lark-whiteboard / lark-shared skills" >&2
fi

echo "NOTE: preflight does not log in to Feishu."
