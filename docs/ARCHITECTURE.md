# Architecture

## Module Map

```
src/obsidian_karpathy/
├── __init__.py       — public API: exports build_graph, __version__
├── cli.py            — Typer CLI entry point (okg); no business logic
├── parser.py         — Markdown parser: wiki links, md links, tags, front matter
├── graph.py          — Graph builder: deduplicates nodes, resolves links, computes stats
├── models.py         — Pydantic models: Node, Edge, Graph, NodeType
└── web.py            — FastAPI app factory: /api/graph endpoint + static UI
```

## Layers (high → low)

```
CLI (cli.py)
    └── Graph builder (graph.py)
            └── Parser (parser.py)
            └── Models (models.py)
Web (web.py)
    └── Graph builder (graph.py)
```

`web.py` and `cli.py` are delivery adapters. Neither imports the other. Both depend only on `graph.py` and `models.py`.

## Data Flow

1. `parser.py` scans each `.md` file in the vault, emitting raw link/tag/metadata records.
2. `graph.py` consumes those records, builds a canonical `Node` set, resolves outbound edges, and surfaces missing-link ghost nodes.
3. `models.py` Pydantic types carry data between all layers.
4. `web.py` serialises the `Graph` to JSON on `GET /api/graph`; the D3 UI reads it on load.
5. `cli.py` drives `build_graph()` for offline JSON dumps, stats tables, and `serve`.

## Invariants

- Parser functions are pure: no I/O, no side effects.
- `build_graph(vault: Path) -> Graph` is the single public entry point for non-delivery code.
- No circular imports: `cli` and `web` may not import each other.
