# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Claude/Anthropic LLM support alongside OpenAI. Configure via `ANTHROPIC_API_KEY` environment variable.
- Auto-detection of LLM provider: uses Claude by default when both OpenAI and Claude keys are present; override with `OKG_OPENAI_PREFER=true`.
- Light/dark theme toggle in the UI sidebar.
- Runtime `Settings` tab with in-memory LLM configuration and chat mode selection (`basic`, `rag`, `tools`).
- Managed job lifecycle endpoints and UI controls for queue/run/cancel flows.
- Pipeline job type that combines summarize + prune analysis for selected notes.

### Changed

- Graph node payload now includes `label`, `markdown`, and `markdown_length` for richer node rendering.
- Graph visualization now scales note blob size by markdown length and emphasizes selected-node neighborhood.
- Inspector now supports markdown preview plus connected-node exploration.

## [0.2.0] - 2026-06-09

### Added

- Root `bun` workflow via `package.json` so `bun run dev` works from repo root.
- LLM endpoints: `GET /api/llm-status` and `POST /api/chat` (OpenAI-compatible).
- Docker multi-stage build with Bun frontend build + Python backend runtime.
- Docker Compose service with optional LLM environment wiring and healthcheck.

### Changed

- README and runbook updated for standalone + Docker workflows.
- API docs updated to current graph schema and LLM endpoints.
- Frontend TypeScript and CSS compatibility fixes (`forceConsistentCasingInFileNames`, Safari blur prefix).
- Root `bun run dev` now launches the Python API and Vite frontend together.

## [0.2.0] - 2026-06-09

### Added

- React/Bun frontend workflow integrated with Python backend for local dev and Docker.
- LLM chat panel and backend endpoints for OpenAI-compatible providers.

### Changed

- Productionization pass across docs, runbook, API schema, testing flow, and deployment paths.

## [0.1.0] - 2026-06-08

### Added

- Initial release of `obsidian-karpathy` / `okg` CLI.
- Markdown parser: Obsidian wiki links (`[[Note]]`, `[[Folder/Note]]`, aliases), Markdown links, front-matter tags, inline hashtags.
- Graph builder: deduplication, ghost nodes for missing links, edge typing (wiki / markdown / tag).
- `okg build` — write graph JSON to disk.
- `okg stats` — print compact vault summary table.
- `okg serve` — FastAPI + D3 force-directed interactive UI at `http://127.0.0.1:8765`.
- `okg init-demo` — copy bundled sample vault for instant exploration.
- Pytest suite with ≥ 80% coverage gate (ships at 94.72%).
- `docs/` canonical engineering docs (ARCHITECTURE, API, TESTING, RUNBOOK, CHANGELOG).
