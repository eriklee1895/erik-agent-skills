#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for erik-agent-skills.
#
# Every skill under skills/ is a self-contained Python script that declares its
# own dependencies inline via PEP 723 and is meant to be run with `uv run`.
# This script installs that native runner plus a single aggregated virtualenv
# (from requirements-dev.txt) so the whole test suite and every skill can be
# exercised without per-skill setup.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# 1. Install uv (PEP 723 runner used by every skill) if it is not present.
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

# 2. Create/refresh the aggregated dev + test virtualenv.
uv venv --python 3.12 .venv
uv pip install -r requirements-dev.txt

# 3. Install the Playwright Chromium browser used by headless scraping skills
#    (e.g. volcengine-doc-fetcher). The WeChat skills instead reuse the system
#    Google Chrome via the CHROME_EXECUTABLE environment variable.
./.venv/bin/python -m playwright install chromium

# 4. Make the toolchain discoverable in interactive shells (idempotent).
BASHRC="$HOME/.bashrc"
add_line() { grep -qsF -- "$1" "$BASHRC" 2>/dev/null || echo "$1" >> "$BASHRC"; }
add_line 'export PATH="$HOME/.local/bin:$PATH"'
if command -v google-chrome >/dev/null 2>&1; then
  add_line "export CHROME_EXECUTABLE=\"$(command -v google-chrome)\""
fi

echo "erik-agent-skills dev environment ready."
echo "  Run a skill:  uv run skills/<skill>/scripts/<name>.py --help"
echo "  Run tests:    ./.venv/bin/python -m pytest skills/"
