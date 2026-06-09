# API

## CLI — `okg`

Installed via `uv sync` / `uv pip install -e .`. Entry point: `okg`.

### Commands

| Command | Args / Options | Description |
|---|---|---|
| `okg build <vault>` | `--output/-o PATH` (default `graph.json`) | Write graph JSON to disk |
| `okg stats <vault>` | — | Print vault summary table |
| `okg serve <vault>` | `--host STR` (default `127.0.0.1`) `--port/-p INT` (default `8765`) `--open/--no-open` | Serve interactive D3 UI |
| `okg init-demo [dest]` | dest defaults to `demo-vault` | Copy bundled sample vault |
| `okg --version` | — | Print installed version |

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Bad argument (typer default) |
| 2 | Vault path does not exist |

## HTTP API (served by `okg serve`)

### `GET /api/graph`

Returns the full graph for the active vault.

**Response schema:**

```json
{
  "nodes": [
    {
      "id": "string",
      "label": "string",
      "type": "note | tag | missing",
      "path": "string | null",
      "tags": ["string"],
      "links": ["string"],
      "summary": "string"
    }
  ],
  "edges": [
    {
      "source": "string",
      "target": "string",
      "type": "wiki | markdown | tag"
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

None required. All configuration is via CLI flags.
