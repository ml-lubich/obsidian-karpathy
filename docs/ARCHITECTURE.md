# Architecture

## Module Map

```
src/obsidian_karpathy/
├── __init__.py       — public API: exports build_graph, __version__
├── cli.py            — Typer CLI entry point (okg); no business logic
├── config.py         — settings model for env / .env runtime configuration
├── parser.py         — Markdown parser: wiki links, md links, tags, front matter
├── graph.py          — Graph builder: deduplicates nodes, resolves links, computes stats
├── llm.py            — OpenAI-compatible chat adapter with basic/rag/tools prompt modes
├── models.py         — Dataclasses for Note, Node, Edge, and KnowledgeGraph
└── web.py            — FastAPI app factory: graph API, runtime settings/jobs APIs, health endpoint, SPA hosting

web/
└── src/              — Bun/Vite React frontend for graph, inspector, AI chat, and runtime settings/jobs
```

## Layers (high → low)

```
CLI (cli.py)
    └── Settings (config.py)
    └── Graph builder (graph.py)
            └── Parser (parser.py)
            └── Models (models.py)
Web (web.py)
    └── Settings (config.py)
    └── LLM adapter (llm.py)
    └── Graph builder (graph.py)
Frontend (web/src)
    └── HTTP API (/api/*)
```

`web.py` and `cli.py` are delivery adapters. Neither imports the other. The React frontend is built
into the Python package for production while Vite proxies to the same FastAPI app in development.

## Data Flow

1. `parser.py` scans each `.md` file in the vault, emitting raw link/tag/metadata records.
2. `graph.py` consumes those records, builds a canonical `Node` set, resolves outbound edges, and surfaces missing-link ghost nodes.
3. `models.py` dataclasses carry data between all layers.
4. `config.py` loads env / `.env` settings for standalone service defaults and LLM configuration.
5. `web.py` serialises the graph to JSON, exposes LLM status/chat/settings/job endpoints, and serves the built React app or packaged fallback UI.
6. `cli.py` drives `build_graph()` for offline JSON dumps, stats tables, and `serve`.

## Invariants

- Parser functions are pure: no I/O, no side effects.
- `build_graph(vault: Path) -> Graph` is the single public entry point for non-delivery code.
- No circular imports: `cli` and `web` may not import each other.
- Missing LLM credentials must disable chat cleanly without breaking graph exploration.
- Runtime settings updates are in-memory only and never write secrets to source files.
