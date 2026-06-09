from pathlib import Path

from fastapi.testclient import TestClient

from obsidian_karpathy.web import create_app


def test_web_app_serves_index_health_and_graph(tmp_path: Path) -> None:
    (tmp_path / "Home.md").write_text("# Home\n\nA note with #tag.", encoding="utf-8")
    client = TestClient(create_app(tmp_path))

    assert client.get("/healthz").json() == {"status": "ok"}

    index = client.get("/")
    assert index.status_code == 200
    assert "<div id=\"root\"></div>" in index.text

    graph = client.get("/api/graph")
    assert graph.status_code == 200
    payload = graph.json()
    assert payload["stats"]["notes"] == 1
    assert payload["nodes"][0]["title"] == "Home"


def test_web_app_reports_llm_status_disabled(tmp_path: Path) -> None:
    (tmp_path / "Home.md").write_text("# Home", encoding="utf-8")
    client = TestClient(create_app(tmp_path))

    assert client.get("/api/llm-status").json()["enabled"] is False
