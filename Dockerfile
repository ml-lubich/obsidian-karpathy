# ── Stage 1: build the React/TypeScript frontend with Bun ─────────────────────
FROM oven/bun:1 AS frontend
WORKDIR /app/web
COPY web/package.json web/bun.lock* ./
RUN bun install --frozen-lockfile
COPY web/ .
RUN bun run build

# ── Stage 2: Python backend ────────────────────────────────────────────────────
FROM python:3.12-slim AS backend
WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/usr/local

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python app and dependencies
COPY README.md VERSION pyproject.toml uv.lock* ./
COPY src/ src/
COPY examples/ examples/
RUN uv sync --frozen --no-dev

# Copy built frontend into the package's static directory
COPY --from=frontend /app/src/obsidian_karpathy/static/dist \
     src/obsidian_karpathy/static/dist

# Vault is mounted at runtime; default to the bundled demo
ENV VAULT_PATH=/data
ENV OPENAI_API_KEY=""
ENV OPENAI_BASE_URL="https://api.openai.com/v1"
ENV OPENAI_MODEL="gpt-4o-mini"

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/healthz')"

# Run as non-root
RUN adduser --system --no-create-home okg
USER okg

CMD ["okg", "serve", "/data", "--host", "0.0.0.0", "--no-open"]
