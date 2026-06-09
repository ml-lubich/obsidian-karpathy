from pathlib import Path

from fastapi.testclient import TestClient

from obsidian_karpathy.web import create_app


def test_web_app_serves_index_health_and_graph(tmp_path: Path) -> None:
    (tmp_path / "Home.md").write_text("# Home\n\nA note with #tag.", encoding="utf-8")
    env_file = tmp_path / ".env"
    client = TestClient(create_app(tmp_path, env_file))

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
    env_file = tmp_path / ".env"
    client = TestClient(create_app(tmp_path, env_file))

    assert client.get("/api/llm-status").json()["enabled"] is False


def test_web_app_can_update_llm_settings_runtime(tmp_path: Path) -> None:
    (tmp_path / "Home.md").write_text("# Home", encoding="utf-8")
    env_file = tmp_path / ".env"
    client = TestClient(create_app(tmp_path, env_file))

    payload = {
        "api_key": "runtime-key",
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.1",
        "mode": "tools",
    }
    updated = client.post("/api/settings/llm", json=payload)

    assert updated.status_code == 200
    assert updated.json()["enabled"] is True
    assert updated.json()["mode"] == "tools"
    
    # Verify settings were persisted to temp .env file
    assert env_file.exists()
    env_content = env_file.read_text()
    assert "OPENAI_API_KEY=runtime-key" in env_content
    assert "OPENAI_BASE_URL=http://localhost:11434/v1" in env_content
    assert "OPENAI_MODEL=llama3.1" in env_content


def test_web_jobs_summarize_and_prune(tmp_path: Path) -> None:
    (tmp_path / "Home.md").write_text("# Home\n\nHello world note", encoding="utf-8")
    (tmp_path / "Sparse.md").write_text("# Sparse\n\nTiny", encoding="utf-8")
    env_file = tmp_path / ".env"
    client = TestClient(create_app(tmp_path, env_file))

    graph = client.get("/api/graph").json()
    note_id = next(node["id"] for node in graph["nodes"] if node["kind"] == "note")
    summarize = client.post("/api/jobs/summarize", json={"node_id": note_id})
    prune = client.post("/api/jobs/prune")
    idle_before = client.post("/api/jobs/run-next")
    run_one = client.post("/api/jobs/run-next")
    run_two = client.post("/api/jobs/run-next")
    jobs = client.get("/api/jobs")

    assert summarize.status_code == 200
    assert summarize.json()["status"] == "queued"
    assert summarize.json()["type"] == "summarize"
    assert prune.status_code == 200
    assert prune.json()["status"] == "queued"
    assert prune.json()["type"] == "prune"
    assert idle_before.status_code == 200
    assert run_one.status_code == 200
    assert run_two.status_code == 200
    assert jobs.status_code == 200
    assert len(jobs.json()) == 2
    assert {jobs.json()[0]["status"], jobs.json()[1]["status"]} == {"completed"}


def test_web_jobs_require_valid_node_id(tmp_path: Path) -> None:
    (tmp_path / "Home.md").write_text("# Home", encoding="utf-8")
    client = TestClient(create_app(tmp_path))

    missing = client.post("/api/jobs/summarize", json={"node_id": ""})
    queued_unknown = client.post("/api/jobs/summarize", json={"node_id": "not-a-node"})
    unknown_result = client.post("/api/jobs/run-next")

    assert missing.status_code == 400
    assert queued_unknown.status_code == 200
    assert unknown_result.status_code == 200
    assert unknown_result.json()["status"] == "failed"


def test_web_settings_endpoint_reports_runtime_metadata(tmp_path: Path) -> None:
    (tmp_path / "Home.md").write_text("# Home", encoding="utf-8")
    client = TestClient(create_app(tmp_path))

    settings = client.get("/api/settings")

    assert settings.status_code == 200
    assert settings.json()["job_count"] == 0
    assert settings.json()["queued_jobs"] == 0
    assert settings.json()["running_jobs"] == 0


def test_web_can_cancel_queued_job(tmp_path: Path) -> None:
    (tmp_path / "Home.md").write_text("# Home\n\nBody", encoding="utf-8")
    client = TestClient(create_app(tmp_path))

    graph = client.get("/api/graph").json()
    note_id = next(node["id"] for node in graph["nodes"] if node["kind"] == "note")
    queued = client.post("/api/jobs/summarize", json={"node_id": note_id}).json()
    cancelled = client.post(f"/api/jobs/{queued['id']}/cancel")

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_web_pipeline_job_runs(tmp_path: Path) -> None:
    (tmp_path / "Home.md").write_text("# Home\n\nBody", encoding="utf-8")
    client = TestClient(create_app(tmp_path))

    graph = client.get("/api/graph").json()
    note_id = next(node["id"] for node in graph["nodes"] if node["kind"] == "note")
    queued = client.post("/api/jobs/pipeline", json={"node_id": note_id})
    ran = client.post("/api/jobs/run-next")

    assert queued.status_code == 200
    assert queued.json()["type"] == "pipeline"
    assert ran.status_code == 200
    assert ran.json()["status"] == "completed"
    assert "summary" in ran.json()["result"]
