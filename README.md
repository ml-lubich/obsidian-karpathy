# Obsidian Karpathy

A Karpathy-inspired knowledge graph explorer for any Obsidian-style Markdown vault. It parses
wiki links, Markdown links, tags, front matter, and summaries, then serves a sleek force-directed
graph with search, filters, stats, and node inspection.

Created by [Misha Lubich](https://mishalubich.com) ([ml-lubich](https://github.com/ml-lubich)).

## Features

- `uv`-native Python project with a small CLI: `okg`
- Obsidian wiki links like `[[Note]]`, `[[Folder/Note]]`, and aliases like `[[Note|Label]]`
- Markdown links to local `.md` files
- Tag nodes from front matter and inline hashtags
- Missing-link nodes so incomplete ideas still appear in the graph
- FastAPI web server with a modern D3 force-directed UI
- Demo vault for instant populated graphs
- Pytest coverage gate set to at least 80%

## Quick Start

```bash
uv sync
uv run okg serve examples/demo-vault
```

Open `http://127.0.0.1:8765` if your browser does not open automatically.

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

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
```

The test suite enforces 80% minimum coverage through `pyproject.toml`.

## Package Metadata

- Website: https://mishalubich.com
- GitHub: https://github.com/ml-lubich
- Repository: https://github.com/ml-lubich/obsidian-karpathy

## License

MIT License. Copyright (c) 2026 Misha Lubich (ml-lubich).
