from __future__ import annotations

import os
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from obsidian_karpathy.graph import build_graph
from obsidian_karpathy.llm import LLMConfig, chat_with_vault


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]


class ChatResponse(BaseModel):
    reply: str


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


def _add_graph_routes(app: FastAPI, root: Path) -> None:
    @app.get("/api/graph")
    def graph() -> JSONResponse:
        return JSONResponse(build_graph(root).to_dict())

    @app.get("/api/llm-status")
    def llm_status() -> dict[str, object]:
        cfg = LLMConfig.from_env()
        return {"enabled": cfg.enabled, "model": cfg.model, "base_url": cfg.base_url}

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(req: ChatRequest) -> ChatResponse:
        cfg = LLMConfig.from_env()
        if not cfg.enabled:
            raise HTTPException(status_code=503, detail="LLM not configured. Set OPENAI_API_KEY.")
        graph_data = build_graph(root).to_dict()
        reply = chat_with_vault(req.messages, graph_data, cfg)
        return ChatResponse(reply=reply)

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


def create_app(vault_path: str | Path) -> FastAPI:
    root = Path(vault_path).expanduser().resolve()
    static_root = Path(str(files("obsidian_karpathy").joinpath("static")))
    frontend_dir = _resolve_frontend_dir()
    app = FastAPI(title="Obsidian Karpathy Graph", docs_url="/api/docs", redoc_url=None)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _mount_static(app, frontend_dir, static_root)
    _add_graph_routes(app, root)
    _add_spa_routes(app, frontend_dir, static_root)
    return app
