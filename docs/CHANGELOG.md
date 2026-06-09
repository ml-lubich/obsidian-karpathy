# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
