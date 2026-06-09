#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
cd "$REPO_ROOT"

VAULT_PATH="${OKG_VAULT_PATH:-examples/demo-vault}"
uv run okg serve "$VAULT_PATH" --host 127.0.0.1 --no-open &
API_PID=$!

cleanup() {
  kill "$API_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM
cd web
bun run dev
