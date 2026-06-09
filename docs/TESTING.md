# Testing

## Verification command

```bash
uv run pytest
```

Runs all tests with coverage. Requires **≥ 80%** statement/line/function/branch coverage — gate enforced via `pytest-cov --cov-fail-under=80`.

## Test layout

```
tests/
├── test_parser.py   — parser unit tests (wiki links, md links, tags, front matter)
├── test_graph.py    — graph builder tests (node dedup, edge resolution, ghost nodes)
├── test_web.py      — FastAPI /api/graph endpoint integration tests
└── test_cli.py      — CLI command smoke tests (build, stats, init-demo)
```

## Definition of Done

A feature is complete when:

1. `uv run pytest` exits 0 with ≥ 80% coverage.
2. New behaviour has at least one behaviour-level test (observable output, not internals).
3. Regression: if a bug is found, a failing test is added before the fix.

## What is intentionally NOT tested

- `okg serve` end-to-end (requires a live uvicorn server; covered by `test_web.py` via FastAPI `TestClient`).
- D3 / frontend JavaScript (no JS test runner configured).
- Demo vault contents (fixture data only, no contract tests).

## Coverage thresholds

Configured in `pyproject.toml` under `[tool.pytest.ini_options]`:

```
--cov=obsidian_karpathy --cov-report=term-missing --cov-fail-under=80
```

No surfaces are intentionally excluded from coverage.
