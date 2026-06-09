# Runbook

## Prerequisites

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

## First-time setup

```bash
git clone git@github.com:ml-lubich/obsidian-karpathy.git
cd obsidian-karpathy
uv sync
```

## Run (demo vault)

```bash
uv run okg serve examples/demo-vault
# opens http://127.0.0.1:8765
```

## Run (your vault)

```bash
uv run okg serve /path/to/your/vault
```

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
uv run pytest
```

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'obsidian_karpathy'` | `src` not on `PYTHONPATH` | Run `uv sync` (ensures editable install). If still broken, add `pythonpath = ["src"]` to `[tool.pytest.ini_options]` in `pyproject.toml` — already present as of v0.1.0. |
| `Address already in use` on port 8765 | Another process holds the port | Pass `--port 9000` (or any free port). |
| Empty graph / 0 nodes | Vault path wrong or no `.md` files | Confirm the path contains `.md` files at any depth. |
| Coverage gate fails | New code not covered | Add a behaviour test; check `--cov-report=term-missing` output for uncovered lines. |

## Adding a new vault feature

1. Add parser support in `src/obsidian_karpathy/parser.py`.
2. Thread through `graph.py` if new node/edge types are needed; update `models.py`.
3. Add behaviour tests in `tests/`.
4. Update `docs/API.md` if the graph JSON schema changed.
5. Run `uv run pytest` — must exit 0.
