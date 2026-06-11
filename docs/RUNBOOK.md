# Runbook

## Prerequisites

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [Bun](https://bun.sh/) for the React frontend and root `bun run ...` workflow

## First-time setup

```bash
git clone git@github.com:ml-lubich/obsidian-knowledge-base.git
cd obsidian-knowledge-base
./scripts/setup.sh
```

`scripts/setup.sh` installs `uv`/`bun` when missing, syncs Python deps, and installs frontend deps.

## LLM Configuration (OpenAI or Claude)

Chat and summarization use an LLM backend. Configure either **OpenAI** or **Claude**:

### OpenAI setup

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o-mini"  # optional; default
uv run okg serve examples/demo-vault
```

### Claude setup

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
uv run okg serve examples/demo-vault
```

Claude is auto-selected when both are set unless you prefer OpenAI:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export OKG_OPENAI_PREFER="true"  # use OpenAI instead of Claude
uv run okg serve examples/demo-vault
```

**Model selection:** Claude defaults to `claude-3-5-sonnet-20241022`. Override via `OKG_ANTHROPIC_MODEL` (currently not a CLI flag; use `.env` or `OKG_` prefix).

- Vite UI: `http://127.0.0.1:5173`
- Python service: `http://127.0.0.1:8765`

The right panel now includes three tabs:

- `Inspector`: click nodes to inspect summary, markdown, and connected nodes.
- `AI Chat`: choose chat mode (`basic`, `rag`, `tools`) via Settings.
- `Settings`: configure runtime LLM endpoint/model/key, queue jobs, run next queued job, and cancel queued/running jobs.

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
| `ModuleNotFoundError: No module named 'obsidian_knowledge_base'` | `src` not on `PYTHONPATH` | Run `uv sync` (ensures editable install). If still broken, add `pythonpath = ["src"]` to `[tool.pytest.ini_options]` in `pyproject.toml` — already present as of v0.1.0. |
| `bun run dev` fails or only starts Vite | Bun deps are missing or the root script is bypassed | Re-run `./scripts/setup.sh`, then run `bun run dev` from the repo root. |
| `Address already in use` on port 8765 | Another process holds the port | Pass `--port 9000` (or any free port). |
| Empty graph / 0 nodes | Vault path wrong or no `.md` files | Confirm the path contains `.md` files at any depth. |
| AI chat tab is disabled | `OPENAI_API_KEY` missing | Add it to `.env` or your shell environment and restart the server. |
| Summarize job returns `node_id is required` | No node selected | Click a note in the graph, then run summarization from `Settings`. |
| Job is queued but no result appears | Queue is paused | Click `Run next queued job` in `Settings` (or call `POST /api/jobs/run-next`). |
| Coverage gate fails | New code not covered | Add a behaviour test; check `--cov-report=term-missing` output for uncovered lines. |

## Adding a new vault feature

1. Add parser support in `src/obsidian_knowledge_base/parser.py`.
2. Thread through `graph.py` if new node/edge types are needed; update `models.py`.
3. Add behaviour tests in `tests/`.
4. Update `docs/API.md` if the graph JSON schema changed.
5. Run `bun run ci` — must exit 0.
