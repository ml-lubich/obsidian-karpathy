#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
cd "$REPO_ROOT"

VAULT_PATH="${OKG_VAULT_PATH:-examples/demo-vault}"
API_LOG="$REPO_ROOT/tmp/api.log"
mkdir -p "$REPO_ROOT/tmp"

# Start API server; redirect its output to a log file so shutdown messages
# don't bleed into the terminal after Ctrl+C.
uv run okg serve "$VAULT_PATH" --host 127.0.0.1 --no-open >"$API_LOG" 2>&1 &
API_PID=$!

cleanup() {
  kill "$API_PID" 2>/dev/null || true
  # Wait briefly so uvicorn finishes its graceful shutdown before the shell reclaims the terminal.
  wait "$API_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "API log → $API_LOG  (tail -f tmp/api.log)"
cd web
bun run dev
