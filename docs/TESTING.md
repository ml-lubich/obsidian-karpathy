# Testing

## Verification command

```bash
bun run ci
```

Runs Python tests with coverage and verifies that the React frontend builds successfully.

## Test layout

```
tests/
├── test_parser.py   — parser unit tests (wiki links, md links, tags, front matter)
├── test_graph.py    — graph builder tests (node dedup, edge resolution, ghost nodes)
├── test_web.py      — FastAPI graph / health / settings / jobs integration tests
├── test_llm.py      — LLM configuration + mode/summarization behavior tests
├── test_config.py   — settings model unit tests
└── test_cli.py      — CLI command smoke tests (build, stats, init-demo)
```

## Definition of Done

A feature is complete when:

1. `uv run pytest` exits 0 with ≥ 80% coverage.
2. `cd web && bun run ci` exits 0.
2. New behaviour has at least one behaviour-level test (observable output, not internals).
3. Regression: if a bug is found, a failing test is added before the fix.

## What is intentionally NOT tested

- `okg serve` end-to-end (requires a live uvicorn server; covered by `test_web.py` via FastAPI `TestClient`).
- D3 / frontend JavaScript runtime behavior (no browser test runner configured).
- React type/build checks are covered by `bun run ci`.
- Demo vault contents (fixture data only, no contract tests).

## Coverage thresholds

Configured in `pyproject.toml` under `[tool.pytest.ini_options]`:

```
--cov=obsidian_knowledge_base --cov-report=term-missing --cov-fail-under=80
```

No surfaces are intentionally excluded from coverage.
