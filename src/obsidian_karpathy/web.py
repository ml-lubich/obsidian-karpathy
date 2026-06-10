from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from obsidian_karpathy.graph import build_graph
from obsidian_karpathy.llm import LLMConfig, chat_with_vault, summarize_markdown


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    mode: Literal["basic", "rag", "tools"] = "rag"
    focus_node_id: str = ""


class ChatResponse(BaseModel):
    reply: str


class LLMSettingsRequest(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    mode: Literal["basic", "rag", "tools"] = "rag"
    provider: Literal["openai", "anthropic"] = "openai"


class JobRequest(BaseModel):
    node_id: str = ""


JobType = Literal["summarize", "prune", "pipeline"]
JobStatus = Literal["queued", "running", "completed", "failed", "cancelled"]


@dataclass(slots=True)
class JobRecord:
    id: str
    type: JobType
    status: JobStatus
    created_at: str
    node_id: str = ""
    started_at: str = ""
    finished_at: str = ""
    error: str = ""
    result: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeState:
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    mode: Literal["basic", "rag", "tools"] = "rag"
    provider: Literal["openai", "anthropic"] = "openai"
    jobs: dict[str, JobRecord] = field(default_factory=dict)
    queue: list[str] = field(default_factory=list)

def _ensure_env_file(env_path: Path = Path(".env")) -> None:
    """Create .env file from .env.example if .env does not exist."""
    if env_path.exists():
        return
    example = env_path.parent / ".env.example"
    if example.exists():
        env_path.write_text(example.read_text())
        return
    # Fallback: create minimal .env
    env_path.write_text(
        "# Auto-generated .env file\n"
        "OKG_VAULT_PATH=examples/demo-vault\n"
        "OKG_HOST=127.0.0.1\n"
        "OKG_PORT=8765\n"
        "OPENAI_API_KEY=\n"
        "OPENAI_MODEL=gpt-4o-mini\n"
        "OPENAI_BASE_URL=https://api.openai.com/v1\n"
    )


def _read_env_value(key: str, env_path: Path = Path(".env")) -> str:
    """Read a single value from .env file."""
    if not env_path.exists():
        return ""
    content = env_path.read_text()
    # Match key=value, handling quoted strings and empty values
    pattern = rf"^{re.escape(key)}=(.*)$"
    for line in content.split("\n"):
        match = re.match(pattern, line)
        if match:
            val = match.group(1).strip()
            # Remove surrounding quotes if present
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            return val
    return ""


def _write_env_value(key: str, value: str, env_path: Path = Path(".env")) -> None:
    """Write or update a single value in .env file."""
    _ensure_env_file(env_path)
    content = env_path.read_text()
    lines = content.split("\n")
    new_lines = []
    found = False

    for line in lines:
        if re.match(rf"^{re.escape(key)}=", line):
            # Update existing key
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)

    if not found:
        # Add new key at end, before trailing empty line if any
        if new_lines and new_lines[-1] == "":
            new_lines.insert(-1, f"{key}={value}")
        else:
            new_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(new_lines))


def _load_persisted_settings(runtime: RuntimeState, env_path: Path = Path(".env")) -> None:
    """Load persisted LLM settings from .env into RuntimeState."""
    _ensure_env_file(env_path)
    provider = _read_env_value("LLM_PROVIDER", env_path) or "openai"
    runtime.provider = provider  # type: ignore[assignment]
    if provider == "anthropic":
        runtime.api_key = _read_env_value("ANTHROPIC_API_KEY", env_path)
    else:
        runtime.api_key = _read_env_value("OPENAI_API_KEY", env_path)
    runtime.base_url = _read_env_value("OPENAI_BASE_URL", env_path)
    runtime.model = _read_env_value("OPENAI_MODEL", env_path)


def _resolved_llm(runtime: RuntimeState) -> LLMConfig:
    cfg = LLMConfig.from_env()
    runtime_key = runtime.api_key.strip()
    runtime_base = runtime.base_url.strip()
    runtime_model = runtime.model.strip()
    provider = runtime.provider if runtime_key else cfg.provider
    api_key = runtime_key or cfg.api_key
    base_url = runtime_base or cfg.base_url
    model = runtime_model or cfg.model
    return LLMConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        enabled=bool(api_key),
        provider=provider,
    )


def _llm_status(runtime: RuntimeState) -> dict[str, object]:
    cfg = _resolved_llm(runtime)
    source = "runtime" if runtime.api_key.strip() else "env"
    return {
        "enabled": cfg.enabled,
        "model": cfg.model,
        "base_url": cfg.base_url,
        "mode": runtime.mode,
        "api_key_source": source,
        "provider": cfg.provider,
    }


def _job_counts(runtime: RuntimeState) -> dict[str, int]:
    queued = sum(job.status == "queued" for job in runtime.jobs.values())
    running = sum(job.status == "running" for job in runtime.jobs.values())
    return {"queued": queued, "running": running, "total": len(runtime.jobs)}


def _new_job(kind: JobType, node_id: str = "") -> JobRecord:
    return JobRecord(
        id=str(uuid.uuid4()),
        type=kind,
        status="queued",
        created_at=datetime.now(UTC).isoformat(),
        node_id=node_id,
    )


def _job_json(job: JobRecord) -> dict[str, object]:
    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "node_id": job.node_id,
        "error": job.error,
        "result": job.result,
    }


def _enqueue_job(runtime: RuntimeState, kind: JobType, node_id: str = "") -> dict[str, object]:
    job = _new_job(kind, node_id)
    runtime.jobs[job.id] = job
    runtime.queue.append(job.id)
    return _job_json(job)


def _job_or_404(runtime: RuntimeState, job_id: str) -> JobRecord:
    job = runtime.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job


def _next_queued_job(runtime: RuntimeState) -> JobRecord | None:
    while runtime.queue:
        job_id = runtime.queue.pop(0)
        job = runtime.jobs.get(job_id)
        if job and job.status == "queued":
            return job
    return None


def _job_result(kind: JobType, graph_data: dict[str, object], job: JobRecord, runtime: RuntimeState) -> dict[str, object]:
    if kind == "summarize":
        return _summarize_result(graph_data, job.node_id, runtime)
    if kind == "prune":
        return _prune_result(graph_data)
    summary = _summarize_result(graph_data, job.node_id, runtime)
    prune = _prune_result(graph_data)
    return {"summary": summary, "prune": prune}


def _run_job(runtime: RuntimeState, root: Path, job: JobRecord) -> dict[str, object]:
    job.status = "running"
    job.started_at = datetime.now(UTC).isoformat()
    try:
        graph_data = build_graph(root).to_dict()
        job.result = _job_result(job.type, graph_data, job, runtime)
        job.status = "completed"
    except HTTPException as exc:
        job.status = "failed"
        job.error = str(exc.detail)
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.error = str(exc)
    job.finished_at = datetime.now(UTC).isoformat()
    return _job_json(job)


def _cancel_job(runtime: RuntimeState, job_id: str) -> dict[str, object]:
    job = _job_or_404(runtime, job_id)
    if job.status in {"completed", "failed", "cancelled"}:
        return _job_json(job)
    job.status = "cancelled"
    job.finished_at = datetime.now(UTC).isoformat()
    return _job_json(job)


def _jobs_latest(runtime: RuntimeState, limit: int = 50) -> list[dict[str, object]]:
    items = sorted(runtime.jobs.values(), key=lambda item: item.created_at, reverse=True)
    return [_job_json(job) for job in items[:limit]]


def _note_by_id(graph_data: dict[str, object], node_id: str) -> dict[str, object] | None:
    for node in graph_data.get("nodes", []):
        if node.get("id") == node_id and node.get("kind") == "note":
            return node
    return None


def _summarize_result(graph_data: dict[str, object], node_id: str, runtime: RuntimeState) -> dict[str, object]:
    note = _note_by_id(graph_data, node_id)
    if note is None:
        raise HTTPException(status_code=404, detail=f"Note node not found: {node_id}")
    summary = summarize_markdown(str(note.get("markdown", "")), str(note.get("title", "")), _resolved_llm(runtime))
    return {"node_id": node_id, "title": note.get("title", ""), "summary": summary}


def _prune_result(graph_data: dict[str, object]) -> dict[str, object]:
    nodes = graph_data.get("nodes", [])
    candidates = []
    for node in nodes:
        if node.get("kind") != "note":
            continue
        degree = int(node.get("backlinks", 0)) + int(node.get("outlinks", 0))
        sparse = degree <= 1 and int(node.get("word_count", 0)) < 80
        if sparse:
            candidates.append({"id": node.get("id", ""), "title": node.get("title", ""), "degree": degree})
    return {"candidate_count": len(candidates), "candidates": candidates[:20]}


def _resolve_frontend_dir() -> Path | None:
    env_dir = os.environ.get("OKG_FRONTEND_DIR", "")
    if env_dir:
        p = Path(env_dir)
        return p if p.is_dir() else None
    candidate = Path(__file__).parent / "static" / "dist"
    return candidate if candidate.is_dir() else None


def _mount_static(app: FastAPI, frontend_dir: Path | None, fallback: Path) -> None:
    if frontend_dir:
        assets_dir = frontend_dir / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        return
    app.mount("/static", StaticFiles(directory=str(fallback)), name="static")


def _add_graph_routes(app: FastAPI, root: Path, runtime: RuntimeState, env_path: Path = Path(".env")) -> None:
    @app.get("/api/graph")
    def graph() -> JSONResponse:
        return JSONResponse(build_graph(root).to_dict())

    @app.get("/api/llm-status")
    def llm_status() -> dict[str, object]:
        return _llm_status(runtime)

    @app.get("/api/settings")
    def settings() -> dict[str, object]:
        status = _llm_status(runtime)
        status["job_count"] = _job_counts(runtime)["total"]
        status["queued_jobs"] = _job_counts(runtime)["queued"]
        status["running_jobs"] = _job_counts(runtime)["running"]
        return status

    @app.post("/api/settings/llm")
    def update_llm_settings(req: LLMSettingsRequest) -> dict[str, object]:
        runtime.provider = req.provider
        _write_env_value("LLM_PROVIDER", req.provider, env_path)
        if req.api_key.strip():
            runtime.api_key = req.api_key.strip()
            key_name = "ANTHROPIC_API_KEY" if req.provider == "anthropic" else "OPENAI_API_KEY"
            _write_env_value(key_name, runtime.api_key, env_path)
        if req.base_url.strip():
            runtime.base_url = req.base_url.strip()
            _write_env_value("OPENAI_BASE_URL", runtime.base_url, env_path)
        if req.model.strip():
            runtime.model = req.model.strip()
            _write_env_value("OPENAI_MODEL", runtime.model, env_path)
        runtime.mode = req.mode
        return _llm_status(runtime)

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(req: ChatRequest) -> ChatResponse:
        cfg = _resolved_llm(runtime)
        if not cfg.enabled:
            raise HTTPException(status_code=503, detail="LLM not configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")
        graph_data = build_graph(root).to_dict()
        mode = req.mode or runtime.mode
        reply = chat_with_vault(req.messages, graph_data, cfg, mode=mode, focus_node_id=req.focus_node_id)
        return ChatResponse(reply=reply)

    @app.post("/api/jobs/summarize")
    def summarize_job(req: JobRequest) -> dict[str, object]:
        if not req.node_id:
            raise HTTPException(status_code=400, detail="node_id is required")
        return _enqueue_job(runtime, "summarize", req.node_id)

    @app.post("/api/jobs/prune")
    def prune_job() -> dict[str, object]:
        return _enqueue_job(runtime, "prune")

    @app.post("/api/jobs/pipeline")
    def pipeline_job(req: JobRequest) -> dict[str, object]:
        if not req.node_id:
            raise HTTPException(status_code=400, detail="node_id is required")
        return _enqueue_job(runtime, "pipeline", req.node_id)

    @app.post("/api/jobs/run-next")
    def run_next_job() -> dict[str, object]:
        next_job = _next_queued_job(runtime)
        if next_job is None:
            return {"status": "idle", "detail": "No queued jobs."}
        if next_job.status == "cancelled":
            return _job_json(next_job)
        return _run_job(runtime, root, next_job)

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict[str, object]:
        return _cancel_job(runtime, job_id)

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, object]:
        return _job_json(_job_or_404(runtime, job_id))

    @app.get("/api/jobs")
    def list_jobs() -> list[dict[str, object]]:
        return _jobs_latest(runtime)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}


def _add_spa_routes(app: FastAPI, frontend_dir: Path | None, fallback: Path) -> None:
    index_path = (frontend_dir / "index.html") if frontend_dir else Path(str(fallback / "index.html"))

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(index_path))

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/") or full_path == "healthz":
            raise HTTPException(status_code=404)
        return FileResponse(str(index_path))


def create_app(vault_path: str | Path, env_path: str | Path | None = None) -> FastAPI:
    root = Path(vault_path).expanduser().resolve()
    static_root = Path(str(files("obsidian_karpathy").joinpath("static")))
    frontend_dir = _resolve_frontend_dir()
    runtime = RuntimeState()
    
    # Ensure .env exists and load persisted settings
    env_file = Path(env_path) if env_path else Path(".env")
    _ensure_env_file(env_file)
    _load_persisted_settings(runtime, env_file)
    
    app = FastAPI(title="Obsidian Karpathy Graph", docs_url="/api/docs", redoc_url=None)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _mount_static(app, frontend_dir, static_root)
    _add_graph_routes(app, root, runtime, env_file)
    _add_spa_routes(app, frontend_dir, static_root)
    return app
