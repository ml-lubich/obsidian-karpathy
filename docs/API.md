# API

## CLI — `okg`

Installed via `uv sync` / `uv pip install -e .`. Entry point: `okg`.

### Commands

| Command | Args / Options | Description |
|---|---|---|
| `okg build <vault>` | `--output/-o PATH` (default `graph.json`) | Write graph JSON to disk |
| `okg stats <vault>` | — | Print vault summary table |
| `okg serve [vault]` | `--host STR` `--port/-p INT` `--open/--no-open` | Serve interactive UI; vault / host / port may also come from env or `.env` |
| `okg init-demo [dest]` | dest defaults to `demo-vault` | Copy bundled sample vault |
| `okg --version` | — | Print installed version |

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Bad argument (typer default) |
| 2 | Vault path does not exist |

If `vault` is omitted for `okg serve`, the server falls back to `OKG_VAULT_PATH`.

## HTTP API (served by `okg serve`)

### `GET /api/graph`

Returns the full graph for the active vault.

**Response schema:**

```json
{
  "nodes": [
    {
      "id": "string",
      "title": "string",
      "kind": "note | tag | missing",
      "path": "string | null",
      "tags": ["string"],
      "summary": "string",
      "word_count": 0,
      "backlinks": 0,
      "outlinks": 0
    }
  ],
  "edges": [
    {
      "source": "string",
      "target": "string",
      "kind": "wiki | markdown | tag",
      "label": "string"
    }
  ],
  "stats": {
    "vault": "string",
    "notes": 0,
    "tags": 0,
    "missing": 0,
    "edges": 0
  }
}
```

### `GET /api/llm-status`

Returns whether chat is enabled and which model endpoint is configured.

```json
{
  "enabled": true,
  "model": "gpt-4o-mini",
  "base_url": "https://api.openai.com/v1"
}
```

### `POST /api/chat`

Chat with your vault context using any OpenAI-compatible backend.

Request body:

```json
{
  "messages": [
    { "role": "user", "content": "What notes discuss spaced repetition?" }
  ]
}
```

Response body:

```json
{
  "reply": "You have notes under Resources including Spaced Repetition..."
}
```

### `GET /healthz`

Container/runtime health endpoint.

```json
{ "status": "ok" }
```

## Python API

```python
from obsidian_karpathy import build_graph

graph = build_graph(Path("my-vault"))
graph.nodes        # list[Node]
graph.edges        # list[Edge]
graph.stats        # dict[str, int | str]
graph.to_dict()    # JSON-serialisable dict
```

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OKG_VAULT_PATH` | No | empty | Default vault path for `okg serve` |
| `OKG_HOST` | No | `127.0.0.1` | Default standalone service host |
| `OKG_PORT` | No | `8765` | Default standalone service port |
| `OPENAI_API_KEY` | No | empty | Enables LLM chat when set |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Chat model |
| `OKG_FRONTEND_DIR` | No | empty | Optional override for built frontend folder |

## Root Bun workspace commands

| Command | Purpose |
|---|---|
| `bun run dev` | Start the Python API and Vite frontend together |
| `bun run serve` | Run the standalone Python service only |
| `bun run build` | Build the React frontend into the packaged Python static directory |
| `bun run ci` | Run Python tests and frontend build verification |
