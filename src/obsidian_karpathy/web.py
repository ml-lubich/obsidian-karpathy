from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from obsidian_karpathy.graph import build_graph


def create_app(vault_path: str | Path) -> FastAPI:
    root = Path(vault_path).expanduser().resolve()
    static_root = files("obsidian_karpathy").joinpath("static")
    app = FastAPI(title="Obsidian Karpathy Graph")

    app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(static_root.joinpath("index.html")))

    @app.get("/api/graph")
    def graph() -> JSONResponse:
        return JSONResponse(build_graph(root).to_dict())

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
