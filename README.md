# Obsidian Knowledge Base

A knowledge graph explorer for any Obsidian-style Markdown vault, inspired by
[Andrej Karpathy](https://karpathy.ai/)'s practical, model-first approach to building tools.
It parses wiki links, Markdown links, tags, front matter, and summaries, then serves a sleek
force-directed graph with search, filters, stats, and node inspection.

Created by [Misha Lubich](https://mishalubich.com) ([ml-lubich](https://github.com/ml-lubich)).

## Features

- `uv`-native Python project with a small CLI: `okg`
- Obsidian wiki links like `[[Note]]`, `[[Folder/Note]]`, and aliases like `[[Note|Label]]`
- Markdown links to local `.md` files
- Tag nodes from front matter and inline hashtags
- Missing-link nodes so incomplete ideas still appear in the graph
- FastAPI web server with a modern D3 force-directed UI
- Dark/light mode toggle and settings panel
- Configurable chat modes (`basic`, `rag`, `tools`) and runtime LLM endpoint/model settings
- Summarization and pruning job controls for agentic-style maintenance loops
- Demo vault for instant populated graphs
- Pytest coverage gate set to at least 80%

## Setup

```bash
./scripts/setup.sh
```

## Quick Start

```bash
bun run dev
```

Run this from the repo root. It starts:

- the Python API on `http://127.0.0.1:8765`
- the Bun/Vite frontend on `http://127.0.0.1:5173`

## Standalone service

```bash
uv run okg serve examples/demo-vault
```

Open `http://127.0.0.1:8765` if your browser does not open automatically.

## Docker

```bash
docker compose up --build
```

This runs the backend and serves the built React frontend at `http://127.0.0.1:8765`.
To use your own vault, replace the mounted `./examples/demo-vault` path in `docker-compose.yml`.

## LLM Wiring (OpenAI-compatible)

Copy `.env.example` to `.env` and set your key if your local `.env` does not already exist:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

Any OpenAI-compatible endpoint works (OpenAI, Ollama, Groq, etc.).

## CLI

```bash
# Serve the interactive graph UI
uv run okg serve /path/to/your/obsidian-vault

# Write graph JSON
uv run okg build /path/to/your/obsidian-vault --output graph.json

# Print a vault summary
uv run okg stats /path/to/your/obsidian-vault

# Copy a packaged demo vault
uv run okg init-demo my-demo-vault
```

## Graph Model

The generated graph contains three node kinds:

- `note`: Markdown files in the vault
- `tag`: tags discovered from front matter and inline hashtags
- `missing`: unresolved wiki links, useful for planned notes

Edges are typed as `wiki`, `markdown`, or `tag`.

Note nodes expose:

- `short_label`: compact 1-3 word graph label
- `markdown`: attached markdown body for inspector exploration
- `markdown_length`: used to scale node size in the graph

## Development

```bash
uv sync --dev
cd web && bun install
uv run pytest
bun run ci
uv run ruff check .
```

The full repo verification gate is `bun run ci` from the repo root.

## Package Metadata

- Website: https://mishalubich.com
- GitHub: https://github.com/ml-lubich
- Repository: https://github.com/ml-lubich/obsidian-knowledge-base

## License

MIT License. Copyright (c) 2026 Misha Lubich (ml-lubich).
