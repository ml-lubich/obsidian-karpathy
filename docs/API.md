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
      "label": "string",
      "kind": "note | tag | missing",
      "path": "string | null",
      "tags": ["string"],
      "summary": "string",
      "markdown": "string",
      "markdown_length": 0,
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
  "base_url": "https://api.openai.com/v1",
  "mode": "rag",
  "api_key_source": "env | runtime"
}
```

### `POST /api/settings/llm`

Update runtime (in-memory) LLM settings used by chat and summarize jobs.

```json
{
  "api_key": "optional-key",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "mode": "basic | rag | tools"
}
```

### `POST /api/chat`

Chat with your vault context using any OpenAI-compatible backend.

Request body:

```json
{
  "messages": [
    { "role": "user", "content": "What notes discuss spaced repetition?" }
  ],
  "mode": "rag",
  "focus_node_id": "optional-node-id"
}
```

Response body:

```json
{
  "reply": "You have notes under Resources including Spaced Repetition..."
}
```

### `POST /api/jobs/summarize`

Queue a summarization job for a selected note node.

```json
{ "node_id": "projects-graph-explorer" }
```

### `POST /api/jobs/prune`

Queue a pruning analysis job (isolated/low-value note candidates).

### `POST /api/jobs/pipeline`

Queue a pipeline job for a selected note node (summary + prune analysis bundle).

```json
{ "node_id": "projects-graph-explorer" }
```

### `POST /api/jobs/run-next`

Execute the next queued job and return its final state.

Idle response when no jobs are queued:

```json
{ "status": "idle", "detail": "No queued jobs." }
```

### `POST /api/jobs/{job_id}/cancel`

Cancel a queued/running job.

### `GET /api/jobs/{job_id}`

Fetch a single job by id.

Response shape for both job endpoints:

```json
{
  "id": "uuid",
  "type": "summarize | prune | pipeline",
  "status": "queued | running | completed | failed | cancelled",
  "created_at": "ISO-8601 timestamp",
  "started_at": "ISO-8601 timestamp",
  "finished_at": "ISO-8601 timestamp",
  "node_id": "optional-node-id",
  "error": "optional-error-message",
  "result": {}
}
```

### `GET /api/jobs`

List recent runtime jobs (latest first).

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
