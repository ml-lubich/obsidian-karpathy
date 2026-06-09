# Runbook

## Prerequisites

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [Bun](https://bun.sh/) for the React frontend and root `bun run ...` workflow

## First-time setup

```bash
git clone git@github.com:ml-lubich/obsidian-karpathy.git
cd obsidian-karpathy
./scripts/setup.sh
```

`scripts/setup.sh` installs `uv`/`bun` when missing, syncs Python deps, and installs frontend deps.

## Run (full development stack)

```bash
bun run dev
```

- Vite UI: `http://127.0.0.1:5173`
- Python service: `http://127.0.0.1:8765`

## Run (demo vault standalone)

```bash
uv run okg serve examples/demo-vault
# opens http://127.0.0.1:8765
```

## Run (your vault)

```bash
uv run okg serve /path/to/your/vault
```

Or set `OKG_VAULT_PATH=/path/to/your/vault` and run `uv run okg serve --no-open`.

## Build graph JSON

```bash
uv run okg build /path/to/vault --output graph.json
```

## Initialise a local demo vault

```bash
uv run okg init-demo my-vault
uv run okg serve my-vault
```

## Tests

```bash
bun run ci
```

## Docker

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8765`.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'obsidian_karpathy'` | `src` not on `PYTHONPATH` | Run `uv sync` (ensures editable install). If still broken, add `pythonpath = ["src"]` to `[tool.pytest.ini_options]` in `pyproject.toml` — already present as of v0.1.0. |
| `bun run dev` fails or only starts Vite | Bun deps are missing or the root script is bypassed | Re-run `./scripts/setup.sh`, then run `bun run dev` from the repo root. |
| `Address already in use` on port 8765 | Another process holds the port | Pass `--port 9000` (or any free port). |
| Empty graph / 0 nodes | Vault path wrong or no `.md` files | Confirm the path contains `.md` files at any depth. |
| AI chat tab is disabled | `OPENAI_API_KEY` missing | Add it to `.env` or your shell environment and restart the server. |
| Coverage gate fails | New code not covered | Add a behaviour test; check `--cov-report=term-missing` output for uncovered lines. |

## Adding a new vault feature

1. Add parser support in `src/obsidian_karpathy/parser.py`.
2. Thread through `graph.py` if new node/edge types are needed; update `models.py`.
3. Add behaviour tests in `tests/`.
4. Update `docs/API.md` if the graph JSON schema changed.
5. Run `bun run ci` — must exit 0.
